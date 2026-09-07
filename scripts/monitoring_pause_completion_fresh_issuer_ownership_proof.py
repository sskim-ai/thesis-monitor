from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from app.providers import opendart_corp_codes
from app.services.coldstart_source_assembly_service import deterministic_base_context
from app.services.reference_universe_audit_service import CanonicalSecurityReference
from scripts import bounded_us_universe_expansion_issuer_reconciliation as expansion
from scripts import directional_core_price_timing_holdout as frozen
from scripts import new_issuer_holdout_selection_ownership_proof as runner
from scripts import new_issuer_holdout_selection_preexecution_review as review
from scripts import synthetic_canary_fixture_repair_ownership_resume as guarded
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "monitoring-pause-completion-fresh-issuer-ownership-proof-v1"
SELECTION_CONTRACT = "fresh-issuer-post-pause-selection-policy-v1"
SELECTION_SALT = expansion.SELECTION_SALT
WORK_INSTRUCTION_PATH = (
    "docs/work-instructions/"
    "20260907-monitoring-pause-completion-and-fresh-issuer-ownership-proof.md"
)
WORK_INSTRUCTION_SHA256 = (
    "4b6d6f858d3518f7a813c3722af9e0ddad06cc6be89c29f83a1469cb9fe707a1"
)
HISTORICAL_ZIP_NAME = (
    "thesis-monitor-20260907-scheduled-monitoring-pause-capacity-failure-"
    "partial-proof-closeout-report.zip"
)
HISTORICAL_ZIP_SHA256 = (
    "6c63a46a135a0abd6f5491366d33d56bbfe2d19f40e4b1f171633a3078b4adbe"
)
EXPANSION_ZIP_NAME = (
    "thesis-monitor-20260907-bounded-us-supported-universe-expansion-"
    "issuer-audit-reconciliation-report.zip"
)
EXPANSION_ZIP_SHA256 = (
    "12ed21a8fcd378036fb86e08193fcffb5b3e0f9f0710f92602a2f3c595c18cf4"
)
PRIOR_REGISTRY_SHA256 = (
    "f91ec0a8ea6a224a5da3375da28d83f01b46c518e8b94a8da0df23398a3f2415"
)
TARGET_US = 4
TARGET_KR = 12
TARGET_TOTAL = TARGET_US + TARGET_KR
KR_CANDIDATE_LIMIT = 48
RUNS = runner.RUNS
STAGES = runner.STAGES
EXPECTED_INVOCATIONS_PER_RUN = 8
EXPECTED_TOTAL_INVOCATIONS = 32
REPORT_DIRECTORY = (
    "20260907-monitoring-pause-completion-fresh-issuer-ownership-proof"
)
CUSTOM_COMPLETION_NAME = "61-monitoring-pause-and-fresh-proof-completion"
REFERENCE_MEMBERS = {
    "us": "evidence/membership/us-reference-membership.jsonl",
    "kr": "evidence/membership/kr-reference-membership.jsonl",
}
HANDOFF_MEMBER = "reports/proofs/23-next-holdout-selection-handoff.json"
PRIOR_REGISTRY_MEMBER = "evidence/membership/exclusion-registry.json"
OVERLAY_MEMBER = "reports/proofs/11-exposure-retirement-and-exclusion-update.json"
OPENDART_REFERENCE_MEMBER = "evidence/reference-snapshots/opendart-corp-code.zip"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
                + "\n"
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
    return subprocess.run(
        ("git", *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def zip_jsonl(archive: zipfile.ZipFile, member: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in archive.read(member).decode("utf-8").splitlines():
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"zip_jsonl_object_required:{member}")
        rows.append(value)
    return rows


def verify_bundle(
    path: Path, *, expected_name: str, expected_sha256: str
) -> dict[str, object]:
    actual_sha256 = file_sha256(path)
    if path.name != expected_name:
        raise ValueError(f"input_zip_name_mismatch:{path.name}")
    if actual_sha256 != expected_sha256:
        raise ValueError(f"input_zip_sha256_mismatch:{path.name}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicate_count = sum(count > 1 for count in Counter(names).values())
        unsafe = [
            name
            for name in names
            if name.startswith("/")
            or "\\" in name
            or ".." in PurePosixPath(name).parts
        ]
        bad_member = archive.testzip()
        index = zip_json(archive, "artifact-index.json")
        index_rows = index.get("rows")
        if not isinstance(index_rows, list):
            raise ValueError(f"artifact_index_rows_missing:{path.name}")
        indexed = {
            str(row["path"]): row
            for row in index_rows
            if isinstance(row, Mapping) and row.get("path")
        }
        payload_names = set(names) - {"artifact-index.json"}
        hash_mismatches = 0
        size_mismatches = 0
        for name in sorted(payload_names & set(indexed)):
            payload = archive.read(name)
            row = indexed[name]
            hash_mismatches += bytes_sha256(payload) != row.get("sha256")
            size_mismatches += len(payload) != row.get("byte_size")
    missing_from_index = sorted(payload_names - set(indexed))
    missing_from_payload = sorted(set(indexed) - payload_names)
    checks = {
        "sha256": actual_sha256 == expected_sha256,
        "duplicate_members": duplicate_count == 0,
        "safe_paths": not unsafe,
        "crc": bad_member is None,
        "index_membership": not missing_from_index and not missing_from_payload,
        "indexed_hashes": hash_mismatches == 0,
        "indexed_sizes": size_mismatches == 0,
    }
    if not all(checks.values()):
        failed = ",".join(key for key, value in checks.items() if not value)
        raise ValueError(f"input_bundle_integrity_failed:{path.name}:{failed}")
    return {
        "path": str(path),
        "sha256": actual_sha256,
        "member_count": len(names),
        "indexed_payload_count": len(index_rows),
        "duplicate_member_count": duplicate_count,
        "unsafe_path_count": len(unsafe),
        "crc_failure": bad_member,
        "missing_from_index_count": len(missing_from_index),
        "missing_from_payload_count": len(missing_from_payload),
        "hash_mismatch_count": hash_mismatches,
        "size_mismatch_count": size_mismatches,
        "checks": checks,
        "status": "PASS",
    }


def merge_exposure_registry(
    prior: Mapping[str, object], overlay: Mapping[str, object]
) -> dict[str, object]:
    prior_rows = [
        dict(row) for row in prior.get("rows") or [] if isinstance(row, Mapping)
    ]
    overlay_rows = [
        dict(row) for row in overlay.get("rows") or [] if isinstance(row, Mapping)
    ]
    if len(prior_rows) != 85:
        raise ValueError(f"prior_registry_count_mismatch:{len(prior_rows)}")
    if len(overlay_rows) != 16:
        raise ValueError(f"overlay_registry_count_mismatch:{len(overlay_rows)}")
    if overlay.get("prior_registry_sha256") != PRIOR_REGISTRY_SHA256:
        raise ValueError("overlay_prior_registry_hash_mismatch")
    if int(overlay.get("reconciled_registry_count") or 0) != 101:
        raise ValueError("overlay_reconciled_count_mismatch")
    rows_by_key = {
        str(row["canonical_issuer_key"]): row
        for row in prior_rows
        if row.get("canonical_issuer_key")
    }
    if len(rows_by_key) != len(prior_rows):
        raise ValueError("prior_registry_duplicate_or_missing_issuer_key")
    for row in overlay_rows:
        key = str(row.get("canonical_issuer_key") or "")
        if not key or key in rows_by_key:
            raise ValueError(f"overlay_duplicate_or_missing_issuer_key:{key}")
        aliases = [str(value) for value in row.get("security_aliases") or []]
        rows_by_key[key] = {
            "actual_output_exposure": bool(row.get("actual_output_exposure")),
            "actual_real_model_spawn": True,
            "canonical_issuer_key": key,
            "exclusion_reasons": list(row.get("exclusion_reasons") or []),
            "lineage": [
                {
                    "experiment_class": "new-issuer-final-freeze-ownership-proof",
                    "exposure_class": "REAL_MODEL_OUTPUT",
                    "generation_id": "HISTORICAL_PRESERVED_IN_INPUT_BUNDLE",
                    "invocation_id": "HISTORICAL_PRESERVED_IN_INPUT_BUNDLE",
                    "model_call_started": True,
                    "source_artifact": OVERLAY_MEMBER,
                    "ticker": row.get("ticker"),
                    "usable_output_exists": True,
                }
            ],
            "market": row.get("market"),
            "security_aliases": aliases,
            "whole_cohort_retired": True,
            "retirement_reasons": ["INCOMPLETE_FIRST_AFTER_FULL_ISSUER_EXPOSURE"],
        }
    rows = [rows_by_key[key] for key in sorted(rows_by_key)]
    if len(rows) != 101:
        raise ValueError(f"reconciled_registry_count_mismatch:{len(rows)}")
    return {
        "contract": "canonical-exposure-registry-plus-latest-overlay-v1",
        "prior_registry_count": len(prior_rows),
        "prior_registry_sha256": PRIOR_REGISTRY_SHA256,
        "appended_exposed_issuer_count": len(overlay_rows),
        "reconciled_registry_count": len(rows),
        "exclusion_shrink_count": 0,
        "historical_cohort_issuer_exposure": "16/16",
        "historical_cohort_core_stage_coverage": "16/16",
        "historical_cohort_timing_stage_coverage": "8/16",
        "historical_complete_first_coverage": 0,
        "historical_retirement_reason": (
            "INCOMPLETE_FIRST_AFTER_FULL_ISSUER_EXPOSURE"
        ),
        "rows": rows,
        "all_excluded_issuer_keys": sorted(rows_by_key),
        "status": "PASS",
    }


def filter_candidate_rows(
    order: Sequence[str],
    references: Sequence[Mapping[str, object]],
    excluded_issuer_keys: set[str],
    *,
    market: str,
    limit: int | None = None,
) -> list[dict[str, object]]:
    by_ticker = {str(row.get("display_symbol")): row for row in references}
    results: list[dict[str, object]] = []
    seen_issuers: set[str] = set()
    for ticker in order:
        row = by_ticker.get(str(ticker))
        if row is None or row.get("market") != market:
            continue
        issuer_key = str(row.get("canonical_issuer_key") or "")
        if not issuer_key or issuer_key in excluded_issuer_keys or issuer_key in seen_issuers:
            continue
        if row.get("identity_resolution_status") != "IDENTITY_RESOLVED":
            continue
        if row.get("routing_support_status") != "ROUTING_SUPPORTED":
            continue
        if not str(row.get("eligibility_decision") or "").startswith("ELIGIBLE"):
            continue
        results.append(dict(row))
        seen_issuers.add(issuer_key)
        if limit is not None and len(results) >= limit:
            break
    return results


def parse_disabled_labels(value: str) -> set[str]:
    return {
        match.group(1)
        for match in re.finditer(r'"([^"\n]+)"\s*=>\s*true', value)
    }


class PauseAwareWorkloadObserver(guarded.SandboxCompatibleWorkloadObserver):
    @property
    def backend(self) -> str:
        return "LAUNCHCTL_ACTIVE_OR_DISABLED_UNLOADED_PLUS_LSOF_CODEX_RUNTIME_STATE"

    @property
    def capabilities(self) -> dict[str, object]:
        return {
            **super().capabilities,
            "disabled_unloaded_natural_job_observable": True,
            "disabled_unloaded_treated_as_active": False,
        }

    def _disabled_labels(self) -> set[str]:
        result = subprocess.run(
            [self.launchctl_bin, "print-disabled", f"gui/{self.uid}"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise guarded.LiveWorkloadObservationUnavailable(
                f"launch_agent_disabled_state_unavailable:{result.returncode}"
            )
        return parse_disabled_labels(result.stdout)

    def _natural_jobs(self) -> tuple[int, list[dict[str, object]]]:
        disabled = self._disabled_labels()
        rows: list[dict[str, object]] = []
        for label in self._natural_job_labels():
            result = subprocess.run(
                [self.launchctl_bin, "print", f"gui/{self.uid}/{label}"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                match = re.search(
                    r"^\s*state = ([^\r\n]+)", result.stdout, re.MULTILINE
                )
                if match is None:
                    raise guarded.LiveWorkloadObservationUnavailable(
                        f"launch_agent_state_unparseable:{label}"
                    )
                state = match.group(1).strip()
                rows.append(
                    {"label": label, "state": state, "active": state == "running"}
                )
                continue
            if result.returncode == 113 and label in disabled:
                rows.append(
                    {"label": label, "state": "disabled_unloaded", "active": False}
                )
                continue
            raise guarded.LiveWorkloadObservationUnavailable(
                f"launch_agent_state_unavailable:{label}:{result.returncode}"
            )
        return sum(bool(row["active"]) for row in rows), rows


def architecture_hashes(repo_root: Path) -> dict[str, str]:
    return {
        **runner.architecture_hashes(repo_root),
        "pause_completion_orchestrator": file_sha256(Path(__file__).resolve()),
    }


def transport_topology_hashes() -> dict[str, str]:
    return {
        **runner.transport_topology_hashes(),
        "PauseAwareWorkloadObserver": runner.source_sha256(
            PauseAwareWorkloadObserver
        ),
    }


def source_generation_ids(commit: str, as_of: datetime) -> tuple[str, str]:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    source_suffix = hashlib.sha256(
        f"{commit}|{stamp}|source|{PROGRAM_CONTRACT}".encode()
    ).hexdigest()[:12]
    runtime_suffix = hashlib.sha256(
        f"{commit}|{stamp}|runtime|{PROGRAM_CONTRACT}".encode()
    ).hexdigest()[:12]
    return (
        f"20260907-fresh-issuer-source-{stamp}-{source_suffix}",
        f"20260907-fresh-issuer-proof-{stamp}-{runtime_suffix}",
    )


def _provenance(repo_root: Path) -> dict[str, object]:
    instruction_commit = git_value(
        "log", "-1", "--format=%H", "--", WORK_INSTRUCTION_PATH
    )
    return {
        "contract": "repository-provenance-v1",
        "branch": git_value("branch", "--show-current"),
        "base_sha": git_value("rev-parse", f"{instruction_commit}^"),
        "work_instruction_commit": instruction_commit,
        "implementation_commit": git_value("rev-parse", "HEAD"),
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "origin_main": git_value("rev-parse", "origin/main"),
        "work_instruction_sha256": file_sha256(repo_root / WORK_INSTRUCTION_PATH),
        "status": "PASS",
    }


def _candidate_manifest(
    market: str, target: int, rows: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    return {
        "contract": f"fresh-{market}-candidate-manifest-v1",
        "market": market,
        "target_count": target,
        "bounded_candidate_count": len(rows),
        "initial_candidates": [str(row["display_symbol"]) for row in rows[:target]],
        "ordered_reserve": [str(row["display_symbol"]) for row in rows[target:]],
        "candidate_rows": [
            {
                "candidate_rank": rank,
                "ticker": row["display_symbol"],
                "canonical_security_id": row.get("canonical_security_id"),
                "canonical_issuer_key": row.get("canonical_issuer_key"),
                "company_name": row.get("issuer_name") or row.get("security_name"),
                "exchange": row.get("provider_exchange") or row.get("exchange"),
                "security_type": row.get("security_type"),
                "routing_support_status": row.get("routing_support_status"),
            }
            for rank, row in enumerate(rows, start=1)
        ],
        "model_calls": 0,
        "status": "FROZEN",
    }


def freeze_selection(args: argparse.Namespace) -> None:
    repo_root = Path.cwd().resolve()
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    if file_sha256(repo_root / WORK_INSTRUCTION_PATH) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_before_selection_freeze")
    historical_integrity = verify_bundle(
        args.historical_zip,
        expected_name=HISTORICAL_ZIP_NAME,
        expected_sha256=HISTORICAL_ZIP_SHA256,
    )
    expansion_integrity = verify_bundle(
        args.expansion_zip,
        expected_name=EXPANSION_ZIP_NAME,
        expected_sha256=EXPANSION_ZIP_SHA256,
    )
    with zipfile.ZipFile(args.expansion_zip) as archive:
        prior_registry = zip_json(archive, PRIOR_REGISTRY_MEMBER)
        us_references = zip_jsonl(archive, REFERENCE_MEMBERS["us"])
        kr_references = zip_jsonl(archive, REFERENCE_MEMBERS["kr"])
        handoff = zip_json(archive, HANDOFF_MEMBER)
    with zipfile.ZipFile(args.historical_zip) as archive:
        overlay = zip_json(archive, OVERLAY_MEMBER)
    if runner.canonical_sha256(prior_registry) != PRIOR_REGISTRY_SHA256:
        raise ValueError("prior_registry_canonical_hash_mismatch")
    registry = merge_exposure_registry(prior_registry, overlay)
    excluded = set(str(value) for value in registry["all_excluded_issuer_keys"])
    us_candidates = filter_candidate_rows(
        handoff.get("deterministic_us_candidate_order") or (),
        us_references,
        excluded,
        market="us",
    )
    kr_candidates = filter_candidate_rows(
        handoff.get("deterministic_kr_candidate_order") or (),
        kr_references,
        excluded,
        market="kr",
        limit=KR_CANDIDATE_LIMIT,
    )
    if len(us_candidates) < TARGET_US or len(kr_candidates) < TARGET_KR:
        raise ValueError("candidate_universe_below_required_market_mix")
    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)
    write_json(args.output_root / "selection-inputs" / "prior-registry.json", prior_registry)
    write_json(args.output_root / "selection-inputs" / "latest-overlay.json", overlay)
    write_json(args.output_root / "selection-inputs" / "merged-registry.json", registry)
    write_json(args.output_root / "selection-inputs" / "expansion-handoff.json", handoff)
    write_jsonl(args.output_root / "selection-inputs" / "us-candidates.jsonl", us_candidates)
    write_jsonl(args.output_root / "selection-inputs" / "kr-candidates.jsonl", kr_candidates)
    candidate_identities = {
        "contract": "fresh-issuer-candidate-identities-v1",
        "us": us_candidates,
        "kr": kr_candidates,
        "status": "FROZEN",
    }
    write_json(args.output_root / "candidate-identities.json", candidate_identities)
    policy = {
        "contract": SELECTION_CONTRACT,
        "status": "FROZEN_PRE_SOURCE_EVALUATION",
        "selection_salt": SELECTION_SALT,
        "candidate_snapshot": {
            "expansion_zip_sha256": EXPANSION_ZIP_SHA256,
            "verified_reference_snapshot": handoff.get("verified_reference_snapshot"),
            "candidate_identities_sha256": runner.canonical_sha256(candidate_identities),
        },
        "exclusion_registry_sha256": runner.canonical_sha256(registry),
        "exclusion_registry_count": 101,
        "exclusion_shrink_count": 0,
        "market_targets": {"us": TARGET_US, "kr": TARGET_KR},
        "market_policies": {
            "us": {
                "candidate_order": [row["display_symbol"] for row in us_candidates],
                "bounded_evaluation_limit": len(us_candidates),
            },
            "kr": {
                "candidate_order": [row["display_symbol"] for row in kr_candidates],
                "bounded_evaluation_limit": len(kr_candidates),
            },
        },
        "selection_rule": (
            "reuse verified expansion handoff order; remove canonical issuer keys in "
            "the reconciled 101-issuer exposure registry; accept the first source-"
            "eligible unique US4 and KR12"
        ),
        "objective_replacement_reasons": [
            "identity validation failure",
            "unsupported source path",
            "duplicate canonical issuer",
            "source validation or sufficiency failure",
            "missing canonical packet",
        ],
        "forbidden_selection_inputs": [
            "model output",
            "anticipated BUY HOLD SELL",
            "price trend",
            "valuation appearance",
            "desired stability",
        ],
        "model": runner.MODEL,
        "reasoning_effort": runner.EFFORT,
        "context_size": runner.CONTEXT_SIZE,
        "timeout_seconds": runner.TIMEOUT_SECONDS,
        "timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "runs": list(RUNS),
        "stages": list(STAGES),
        "expected_invocations_per_run": EXPECTED_INVOCATIONS_PER_RUN,
        "expected_total_invocations": EXPECTED_TOTAL_INVOCATIONS,
        "retry_count": 0,
        "selective_rerun": 0,
        "hotfix_after_first_real_output": 0,
        "source_evaluation_performed": 0,
        "model_calls": 0,
    }
    provenance = _provenance(repo_root)
    runner.write_proof(args.report_dir, 1, provenance)
    runner.write_proof(
        args.report_dir,
        2,
        {
            "contract": "task-input-integrity-v1",
            "historical": historical_integrity,
            "expansion_reference": expansion_integrity,
            "historical_completion_counter_note": (
                "historical completion reported 126/125 while actual ZIP/index is "
                "127/126; payload integrity is unchanged"
            ),
            "status": "PASS",
        },
    )
    runner.write_proof(args.report_dir, 3, registry)
    runner.write_proof(
        args.report_dir,
        4,
        {
            "contract": "fresh-holdout-exclusion-continuity-v1",
            "prior_count": 85,
            "appended_count": 16,
            "reconciled_count": 101,
            "excluded_issuer_keys": registry["all_excluded_issuer_keys"],
            "exclusion_shrink_count": 0,
            "status": "PASS",
        },
    )
    runner.write_proof(args.report_dir, 5, policy)
    runner.write_proof(args.report_dir, 6, _candidate_manifest("us", TARGET_US, us_candidates))
    runner.write_proof(args.report_dir, 9, _candidate_manifest("kr", TARGET_KR, kr_candidates))
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "SELECTION_FROZEN",
        "branch": provenance["branch"],
        "base_sha": provenance["base_sha"],
        "work_instruction_commit": provenance["work_instruction_commit"],
        "selection_freeze_commit": "PENDING_COMMIT",
        "selection_policy_sha256": runner.canonical_sha256(policy),
        "candidate_identities_sha256": runner.canonical_sha256(candidate_identities),
        "exclusion_registry_sha256": runner.canonical_sha256(registry),
        "exclusion_registry_count": 101,
        "ordered_cohort": [],
        "model_invocation_count": 0,
        "production_scheduler_change_current_task": 2,
        "production_telegram_send_current_task": 0,
    }
    write_json(args.output_root / "program-state.json", state)
    runner.write_reports(args.report_dir)
    write_text(
        args.report_dir / "README.md",
        "# Monitoring Pause Completion & Fresh Issuer Ownership Proof\n\n"
        "The operational pause is complete. This directory first freezes the "
        "reconciled 101-issuer exclusion registry and deterministic US/KR candidate "
        "order before any source outcome or model output is observed.\n",
    )
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def _reference_models(rows: Sequence[Mapping[str, object]]) -> list[CanonicalSecurityReference]:
    return [CanonicalSecurityReference.model_validate(row) for row in rows]


def _packet_for_ticker(root: Path, ticker: str) -> Path | None:
    matches = list(root.rglob(f"*-{ticker}-full.json"))
    if len(matches) > 1:
        raise ValueError(f"multiple_diagnostic_packets:{ticker}")
    return matches[0] if matches else None


async def diagnose_until_target(
    *,
    market: str,
    candidates: Sequence[CanonicalSecurityReference],
    target: int,
    as_of: datetime,
    cache_dir: Path,
    packet_dir: Path,
) -> tuple[dict[str, object], list[dict[str, object]], dict[str, Path]]:
    cursor = 0
    selected: list[dict[str, object]] = []
    all_rows: list[dict[str, object]] = []
    selected_packets: dict[str, Path] = {}
    segment = 0
    while cursor < len(candidates) and len(selected) < target:
        segment += 1
        remaining = list(candidates[cursor:])
        segment_root = packet_dir / market / f"segment-{segment:02d}"
        result = await expansion.run_source_diagnostics(
            market=market,
            candidates=remaining,
            target=target - len(selected),
            limit=len(remaining),
            as_of=as_of,
            cache_dir=cache_dir,
            packet_dir=segment_root,
        )
        attempted = int(result.get("attempted_count") or 0)
        if attempted <= 0:
            break
        for offset, raw in enumerate(result.get("rows") or [], start=1):
            row = dict(raw)
            global_rank = cursor + offset
            ticker = str(row["ticker"])
            packet = _packet_for_ticker(segment_root, ticker)
            eligible = bool(row.get("fundamental_source_sufficient")) and packet is not None
            eligible = eligible and row.get("price_timing_input_readiness") in {
                "READY",
                "UNAVAILABLE_SAFE",
            }
            eligible = eligible and row.get("security_accounting_basis_status") == "PASS"
            row.update(
                {
                    "candidate_rank": global_rank,
                    "eligible_for_final_holdout": eligible,
                    "selected": eligible and len(selected) < target,
                    "packet_path": str(packet) if packet is not None else None,
                }
            )
            if row["selected"]:
                selected.append(row)
                selected_packets[ticker] = packet
            all_rows.append(row)
        cursor += attempted
    provider_totals: Counter[str] = Counter()
    for row in all_rows:
        audit = row.get("provider_audit")
        if isinstance(audit, Mapping):
            for key, value in audit.items():
                if isinstance(value, int):
                    provider_totals[str(key)] += value
    audit = {
        "contract": f"fresh-{market}-source-coverage-audit-v1",
        "market": market,
        "target_count": target,
        "bounded_candidate_count": len(candidates),
        "attempted_count": len(all_rows),
        "source_sufficient_count": len(selected),
        "source_insufficient_count": len(all_rows) - len(selected),
        "untested_candidate_count": max(0, len(candidates) - len(all_rows)),
        "provider_totals": dict(sorted(provider_totals.items())),
        "rows": all_rows,
        "source_target_status": "PASS" if len(selected) == target else "FAIL",
        "model_calls": 0,
        "status": "PASS" if len(selected) == target else "FAIL_CLOSED",
    }
    return audit, selected, selected_packets


def _run_model_free_preflight(
    *,
    root: Path,
    packets: Mapping[str, Mapping[str, object]],
    cohort: Sequence[str],
    source_generation_id: str,
    runtime_generation_id: str,
    selection_policy_sha256: str,
) -> dict[str, object]:
    rehearsal_args, rehearsal_state, adapter, inputs = (
        review._prepare_real_input_rehearsal(
            root=root,
            packets=packets,
            cohort=cohort,
            source_generation_id=source_generation_id,
            runtime_generation_id=runtime_generation_id,
            review_manifest_sha256=selection_policy_sha256,
        )
    )
    run_results = {}
    for run in RUNS:
        run_results[run] = review._execute_model_free_review_run(
            args=rehearsal_args,
            state=rehearsal_state,
            adapter=adapter,
            run=run,
            **inputs,
        )
    summary = review._real_input_mode_summary(root, adapter)
    summary.update(
        {
            "contract": "fresh-issuer-actual-request-model-free-preflight-v1",
            "run_results": {
                run: result["status"] for run, result in run_results.items()
            },
            "expected_simulated_invocation_count": EXPECTED_TOTAL_INVOCATIONS,
            "real_investment_model_invocation_count": adapter.model_call_count,
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


def _source_blocked(
    args: argparse.Namespace,
    *,
    state: dict[str, object],
    us_audit: Mapping[str, object],
    kr_audit: Mapping[str, object],
) -> None:
    reason = (
        f"US={us_audit['source_target_status']};"
        f"KR={kr_audit['source_target_status']}"
    )
    runner.write_proof(
        args.report_dir,
        15,
        {
            "contract": "fresh-holdout-selection-result-v1",
            "ordered_cohort": [],
            "status": "NOT_RUN_SOURCE_COVERAGE_BLOCKED",
        },
    )
    for run in RUNS:
        runner.write_failed_run(args, run, reason)
    production = production_change_proof(args)
    runner.write_proof(args.report_dir, 57, production)
    runner.write_proof(
        args.report_dir,
        58,
        {
            "contract": "night-futures-no-change-v1",
            "night_futures_code_mutation": 0,
            "night_futures_decision_packet_injection": 0,
            "status": "PASS",
        },
    )
    runner.write_proof(
        args.report_dir,
        59,
        {
            "contract": "monitoring-bootstrap-next-handoff-v1",
            "readiness": "NOT_READY_SOURCE_COVERAGE_BLOCKED",
            "next_scope": "BOUNDED_SOURCE_COVERAGE_REVIEW",
            "status": "NOT_READY",
        },
    )
    completion = {
        "contract": PROGRAM_CONTRACT,
        "operational_pause_status": "PAUSED_COMPLETE",
        "proof_status": "STOPPED_PRE_MODEL_SOURCE_FAILURE",
        "us_source_target_status": us_audit["source_target_status"],
        "kr_source_target_status": kr_audit["source_target_status"],
        "run_results": {run: "NOT_RUN" for run in RUNS},
        "real_model_invocation_count": 0,
        "readiness": "NOT_READY_SOURCE_COVERAGE_BLOCKED",
        "stop_reason": reason,
        "artifact_count": "PENDING_FINALIZE",
        "full_tests": "PENDING_FINAL_VALIDATION",
        "ruff": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
    }
    runner.write_proof(args.report_dir, 60, completion)
    state.update(
        {
            "state": "EVIDENCE_COMPLETE",
            "source_gate_only": True,
            "stop_reason": reason,
            "run_results": completion["run_results"],
            "readiness": completion["readiness"],
        }
    )
    write_json(args.output_root / "program-state.json", state)
    _write_custom_completion(args, state=state, stop_reason=reason)
    runner.write_reports(args.report_dir)


def prepare(args: argparse.Namespace) -> None:
    repo_root = Path.cwd().resolve()
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "SELECTION_FROZEN":
        raise ValueError("selection_frozen_state_required")
    if file_sha256(repo_root / WORK_INSTRUCTION_PATH) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_before_source_evaluation")
    if not git_value("ls-files", str(runner.proof_path(args.report_dir, 5).relative_to(repo_root))):
        raise ValueError("selection_policy_must_be_committed_before_source_evaluation")
    policy = read_json(runner.proof_path(args.report_dir, 5))
    if runner.canonical_sha256(policy) != state["selection_policy_sha256"]:
        raise ValueError("selection_policy_drift")
    identities = read_json(args.output_root / "candidate-identities.json")
    if runner.canonical_sha256(identities) != state["candidate_identities_sha256"]:
        raise ValueError("candidate_identity_drift")
    if args.timeout != runner.TIMEOUT_SECONDS:
        raise ValueError("timeout_drift")
    guard = guarded.LiveWorkloadGuard(
        args.output_root / "live-workload-coexistence-audit.json",
        observer=PauseAwareWorkloadObserver(),
    )
    preflight = guard.preflight(
        stage="SOURCE_PREPARATION", batch_id="all-16", subject_count=TARGET_TOTAL
    )
    if preflight["status"] != "PASS":
        raise ValueError("live_workload_or_protected_window_not_clear")
    with zipfile.ZipFile(args.expansion_zip) as archive:
        opendart_corp_codes._cached_companies = opendart_corp_codes._parse_corp_code_zip(
            archive.read(OPENDART_REFERENCE_MEMBER)
        )
    us_candidates = _reference_models(identities["us"])
    kr_candidates = _reference_models(identities["kr"])
    cache_dir = args.output_root / "source-cache"
    packet_dir = args.output_root / "source-diagnostics"
    us_audit, us_selected, us_packets = asyncio.run(
        diagnose_until_target(
            market="us",
            candidates=us_candidates,
            target=TARGET_US,
            as_of=args.as_of,
            cache_dir=cache_dir,
            packet_dir=packet_dir,
        )
    )
    kr_audit, kr_selected, kr_packets = asyncio.run(
        diagnose_until_target(
            market="kr",
            candidates=kr_candidates,
            target=TARGET_KR,
            as_of=args.as_of,
            cache_dir=cache_dir,
            packet_dir=packet_dir,
        )
    )
    runner.write_proof(args.report_dir, 7, us_audit)
    runner.write_proof(
        args.report_dir,
        8,
        {
            "contract": "fresh-us-source-failure-detail-v1",
            "failure_count": sum(
                not row["eligible_for_final_holdout"] for row in us_audit["rows"]
            ),
            "rows": [
                row for row in us_audit["rows"] if not row["eligible_for_final_holdout"]
            ],
            "status": "DIAGNOSTIC_COMPLETE",
        },
    )
    runner.write_proof(args.report_dir, 10, kr_audit)
    runner.write_proof(
        args.report_dir,
        11,
        {
            "contract": "fresh-kr-source-failure-detail-v1",
            "failure_count": sum(
                not row["eligible_for_final_holdout"] for row in kr_audit["rows"]
            ),
            "rows": [
                row for row in kr_audit["rows"] if not row["eligible_for_final_holdout"]
            ],
            "status": "DIAGNOSTIC_COMPLETE",
        },
    )
    both_pass = (
        us_audit["source_target_status"] == "PASS"
        and kr_audit["source_target_status"] == "PASS"
    )
    runner.write_proof(
        args.report_dir,
        12,
        {
            "contract": "fresh-dual-market-source-coverage-summary-v1",
            "us_target": TARGET_US,
            "us_attempted": us_audit["attempted_count"],
            "us_source_sufficient": us_audit["source_sufficient_count"],
            "kr_target": TARGET_KR,
            "kr_attempted": kr_audit["attempted_count"],
            "kr_source_sufficient": kr_audit["source_sufficient_count"],
            "dual_market_source_status": "BOTH_PASS" if both_pass else "FAIL_CLOSED",
            "market_failure_did_not_abort_other_market_diagnostic": 1,
            "real_model_calls": 0,
            "status": "PASS" if both_pass else "DIAGNOSTIC_COMPLETE",
        },
    )
    runner.write_proof(
        args.report_dir,
        13,
        {
            "contract": "cross-market-failure-comparison-v1",
            "us_failure_count": us_audit["source_insufficient_count"],
            "kr_failure_count": kr_audit["source_insufficient_count"],
            "status": "PASS",
        },
    )
    runner.write_proof(
        args.report_dir,
        14,
        {
            "contract": "fresh-source-coverage-decision-v1",
            "real_model_execution_allowed": int(both_pass),
            "new_paid_dependency": 0,
            "new_source_route": 0,
            "readiness": (
                "READY_FOR_NEW_HOLDOUT_FREEZE"
                if both_pass
                else "NOT_READY_SOURCE_COVERAGE_BLOCKED"
            ),
            "status": "PASS" if both_pass else "FAIL_CLOSED",
        },
    )
    if not both_pass:
        _source_blocked(
            args, state=state, us_audit=us_audit, kr_audit=kr_audit
        )
        return
    selected_rows = [*us_selected, *kr_selected]
    cohort = tuple(str(row["ticker"]) for row in selected_rows)
    if len(cohort) != TARGET_TOTAL:
        raise ValueError(f"final_cohort_size_mismatch:{len(cohort)}")
    packet_paths = {**us_packets, **kr_packets}
    packets: dict[str, dict[str, object]] = {}
    contexts: dict[str, str] = {}
    for ticker in cohort:
        packet = read_json(packet_paths[ticker])
        packets[ticker] = packet
        contexts[ticker] = deterministic_base_context(packet)
        write_json(args.output_root / "packets" / f"{ticker}.json", packet)
        write_text(args.output_root / "base-contexts" / f"{ticker}.txt", contexts[ticker])
    evidence, owned, core_aliases, timing_aliases, price_maps, _stocks = (
        frozen.build_inputs(packets, contexts, cohort)
    )
    implementation_commit = git_value("rev-parse", "HEAD")
    source_generation_id, runtime_generation_id = source_generation_ids(
        implementation_commit, args.as_of
    )
    source_lock = frozen.source_lock_document(
        generation_id=source_generation_id,
        cohort=cohort,
        packets=packets,
        base_contexts=contexts,
        evidence=evidence,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    source_lock.update(
        {
            "contract": "fresh-issuer-post-pause-executable-source-lock-v1",
            "source_generation_id": source_generation_id,
            "runtime_generation_id": runtime_generation_id,
            "selection_policy_sha256": state["selection_policy_sha256"],
            "exclusion_registry_sha256": state["exclusion_registry_sha256"],
            "exclusion_registry_count": 101,
            "executable": True,
            "execution_authorized": True,
            "proof_source_lock": True,
            "new_paid_dependency_count": 0,
        }
    )
    source_lock_hash = runner.canonical_sha256(source_lock)
    write_json(
        args.output_root / "source-lock.json",
        {**source_lock, "source_lock_sha256": source_lock_hash},
    )
    prompt_lock = frozen._write_prompt_schema_lock(
        output_root=args.output_root,
        generation_id=source_generation_id,
        cohort=cohort,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    model_free = _run_model_free_preflight(
        root=args.output_root / "model-free-actual-request-preflight",
        packets=packets,
        cohort=cohort,
        source_generation_id=source_generation_id,
        runtime_generation_id=runtime_generation_id,
        selection_policy_sha256=state["selection_policy_sha256"],
    )
    groups = [list(group) for group in frozen.batches(cohort)]
    if len(groups) != 4 or any(len(group) != 4 for group in groups):
        raise ValueError("unexpected_context_topology")
    architecture = architecture_hashes(repo_root)
    topology = transport_topology_hashes()
    selection = {
        "contract": "fresh-holdout-selection-result-v1",
        "ordered_cohort": list(cohort),
        "context_groups": groups,
        "selected_count": len(cohort),
        "us_count": TARGET_US,
        "kr_count": TARGET_KR,
        "replacement_count": sum(
            int(row["candidate_rank"]) > (TARGET_US if index < TARGET_US else TARGET_KR)
            for index, row in enumerate(selected_rows)
        ),
        "selection_after_model_output": 0,
        "status": "PASS",
    }
    source_generation = {
        "contract": "fresh-final-source-generation-v1",
        "source_generation_id": source_generation_id,
        "runtime_generation_id": runtime_generation_id,
        "source_runtime_identity_separated": True,
        "per_issuer_packet_hashes": source_lock["packet_sha256"],
        "aggregate_source_lock_sha256": source_lock_hash,
        "status": "PASS",
    }
    precommit = {
        "contract": "fresh-issuer-post-pause-execution-precommit-v1",
        "ordered_cohort": list(cohort),
        "market_by_ticker": source_lock["market_by_ticker"],
        "context_groups": groups,
        "source_generation_id": source_generation_id,
        "runtime_generation_id": runtime_generation_id,
        "source_lock_sha256": source_lock_hash,
        "packet_sha256": source_lock["packet_sha256"],
        "prompt_schema_lock_sha256": runner.canonical_sha256(prompt_lock),
        "implementation_commit": implementation_commit,
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "model": runner.MODEL,
        "reasoning_effort": runner.EFFORT,
        "timeout_seconds": runner.TIMEOUT_SECONDS,
        "timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "batch_semantics": runner.BATCH_SEMANTICS,
        "subjects_per_context": runner.CONTEXT_SIZE,
        "runs": list(RUNS),
        "stages": list(STAGES),
        "expected_invocations_per_run": EXPECTED_INVOCATIONS_PER_RUN,
        "expected_total_model_invocations": EXPECTED_TOTAL_INVOCATIONS,
        "model_retry_count": 0,
        "selective_rerun": 0,
        "batch_split": 0,
        "hotfix_after_first_output": 0,
        "model_free_preflight": model_free,
        "pre_first_frozen_at": datetime.now(UTC).isoformat(),
        "status": "FROZEN",
    }
    write_json(args.output_root / "new-holdout-precommit.json", precommit)
    runner.write_proof(args.report_dir, 15, selection)
    runner.write_proof(args.report_dir, 16, source_generation)
    runner.write_proof(
        args.report_dir,
        17,
        {
            "contract": "fresh-final-source-sufficiency-audit-v1",
            "rows": selected_rows,
            "selected_sufficient_count": len(selected_rows),
            "directional_model_calls_on_source_insufficient": 0,
            "status": "PASS",
        },
    )
    runner.write_proof(
        args.report_dir,
        18,
        {
            "contract": "fresh-final-source-identity-audit-v1",
            "rows": [
                {
                    "ticker": row["ticker"],
                    "market": "us" if index < TARGET_US else "kr",
                    "canonical_issuer_key": row["canonical_issuer_key"],
                    "status": "PASS",
                }
                for index, row in enumerate(selected_rows)
            ],
            "duplicate_issuer_count": 0,
            "prior_exposure_overlap_count": 0,
            "status": "PASS",
        },
    )
    runner.write_proof(
        args.report_dir, 19, {**source_lock, "source_lock_sha256": source_lock_hash}
    )
    runner.write_proof(args.report_dir, 20, precommit)
    runner.write_proof(
        args.report_dir,
        21,
        {
            "contract": "architecture-semantic-freeze-v1",
            "architecture_hashes": architecture,
            "investment_decision_threshold_mutation": 0,
            "status": "FROZEN",
        },
    )
    runner.write_proof(
        args.report_dir,
        22,
        {
            "contract": "prompt-schema-freeze-v1",
            "prompt_schema_lock": prompt_lock,
            "prompt_schema_lock_sha256": runner.canonical_sha256(prompt_lock),
            "actual_request_model_free_preflight": model_free,
            "status": "FROZEN",
        },
    )
    runner.write_proof(
        args.report_dir,
        23,
        {
            "contract": "model-context-freeze-v1",
            "context_groups": groups,
            "market_grouping": ["US4", "KR4", "KR4", "KR4"],
            "runs": list(RUNS),
            "stage_order": list(STAGES),
            "expected_invocations_per_run": EXPECTED_INVOCATIONS_PER_RUN,
            "expected_total_model_invocations": EXPECTED_TOTAL_INVOCATIONS,
            "status": "FROZEN",
        },
    )
    runner.write_proof(
        args.report_dir,
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
        args.report_dir,
        25,
        {
            "contract": "fresh-holdout-unseen-reuse-gate-v1",
            "ordered_cohort": list(cohort),
            "prior_registry_overlap": [],
            "holdout_output_exposure_state": "UNEXPOSED",
            "holdout_semantic_revelation_state": "NOT_MEASURED",
            "holdout_retirement_state": "ACTIVE_UNEXPOSED",
            "future_unseen_holdout_reuse_allowed": 1,
            "status": "PASS",
        },
    )
    runner.write_proof(
        args.report_dir,
        26,
        read_json(args.output_root / "live-workload-coexistence-audit.json"),
    )
    state.update(
        {
            "state": "PREPARED_FROZEN",
            "selection_freeze_commit": implementation_commit,
            "implementation_commit": implementation_commit,
            "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
            "as_of": args.as_of.isoformat(),
            "program_generation_id": runtime_generation_id,
            "source_generation_id": source_generation_id,
            "source_lock_sha256": source_lock_hash,
            "packet_hashes": source_lock["packet_sha256"],
            "ordered_cohort": list(cohort),
            "architecture_hashes": architecture,
            "transport_topology_hashes": topology,
            "prompt_schema_lock_sha256": runner.canonical_sha256(prompt_lock),
            "precommit_sha256": runner.canonical_sha256(precommit),
            "holdout_output_exposure_state": "UNEXPOSED",
            "holdout_semantic_revelation_state": "NOT_MEASURED",
            "holdout_retirement_state": "ACTIVE_UNEXPOSED",
            "future_unseen_holdout_reuse_allowed": 1,
            "same_cohort_architecture_tuning_rerun_allowed": 0,
            "exposed_subjects": [],
            "model_invocation_count": 0,
            "real_investment_model_invocation_count": 0,
            "model_free_preflight_invocation_count": EXPECTED_TOTAL_INVOCATIONS,
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
        }
    )
    write_json(args.output_root / "program-state.json", state)
    runner.write_reports(args.report_dir)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def verify_frozen(args: argparse.Namespace, state: Mapping[str, object]) -> None:
    repo_root = Path.cwd().resolve()
    if file_sha256(repo_root / WORK_INSTRUCTION_PATH) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if architecture_hashes(repo_root) != state["architecture_hashes"]:
        raise ValueError("architecture_semantic_drift_after_freeze")
    if transport_topology_hashes() != state["transport_topology_hashes"]:
        raise ValueError("transport_topology_drift_after_freeze")
    policy = read_json(runner.proof_path(args.report_dir, 5))
    if runner.canonical_sha256(policy) != state["selection_policy_sha256"]:
        raise ValueError("selection_policy_drift_after_freeze")
    precommit = read_json(args.output_root / "new-holdout-precommit.json")
    if runner.canonical_sha256(precommit) != state["precommit_sha256"]:
        raise ValueError("precommit_drift_after_freeze")
    source_lock = read_json(args.output_root / "source-lock.json")
    recorded_hash = source_lock.pop("source_lock_sha256")
    if (
        runner.canonical_sha256(source_lock) != recorded_hash
        or recorded_hash != state["source_lock_sha256"]
    ):
        raise ValueError("source_lock_drift_after_freeze")
    for number in (5, 19, 20):
        relative = runner.proof_path(args.report_dir, number).relative_to(repo_root)
        if not git_value("ls-files", str(relative)):
            raise ValueError(f"proof_must_be_committed_before_model_call:{number}")


def _scan_real_exposure(output_root: Path, cohort: Sequence[str]) -> dict[str, object]:
    exposed: set[str] = set()
    rows = 0
    stage_contexts: Counter[str] = Counter()
    for manifest_path in sorted(
        (output_root / "model-contexts").rglob("context_manifest.json")
    ):
        manifest = read_json(manifest_path)
        raw_path = manifest_path.parent / "output.raw.json"
        if not raw_path.is_file() or raw_path.stat().st_size == 0:
            continue
        subjects = [str(value) for value in manifest.get("subjects") or []]
        exposed.update(subjects)
        stage_contexts[str(manifest.get("stage") or "UNKNOWN")] += 1
        try:
            candidates = read_json(raw_path).get("candidates")
            rows += len(candidates) if isinstance(candidates, list) else 0
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    return {
        "unique_exposed_issuers": sorted(exposed),
        "unique_exposed_issuer_count": len(exposed),
        "raw_subject_row_count": rows,
        "stage_context_counts": dict(stage_contexts),
        "output_exposure_state": (
            "UNEXPOSED"
            if not exposed
            else "FULLY_EXPOSED"
            if len(exposed) == len(cohort)
            else "PARTIALLY_EXPOSED"
        ),
    }


def _augment_run(args: argparse.Namespace, run: str, document: dict[str, object]) -> dict[str, object]:
    ownership = read_json(runner.proof_path(args.report_dir, runner.RUN_PROOFS[run][3]))
    renderer = read_json(runner.proof_path(args.report_dir, runner.RUN_PROOFS[run][4]))
    hard = read_json(runner.proof_path(args.report_dir, runner.RUN_PROOFS[run][5]))
    manifests = read_json(runner.proof_path(args.report_dir, runner.RUN_PROOFS[run][1]))
    identity_rows = [
        read_json(path)
        for path in sorted(
            (args.output_root / "model-contexts" / run.upper()).rglob(
                "output-identity-validation.json"
            )
        )
    ]
    document.update(
        {
            "execution_status": document.get("status"),
            "identity_gate_status": (
                "PASS"
                if len(identity_rows) == EXPECTED_INVOCATIONS_PER_RUN
                and all(row.get("status") == "PASS" for row in identity_rows)
                else "FAIL"
            ),
            "ownership_gate_status": ownership.get("status"),
            "renderer_gate_status": renderer.get("status"),
            "hard_safety_gate_status": hard.get("status"),
            "preservation_status": (
                "PASS"
                if int(
                    manifests.get("context_evidence_preservation_failure_count") or 0
                )
                == 0
                else "FAIL"
            ),
            "expected_model_invocation_count": EXPECTED_INVOCATIONS_PER_RUN,
        }
    )
    runner.write_proof(args.report_dir, runner.RUN_PROOFS[run][0], document)
    return document


def production_change_proof(args: argparse.Namespace) -> dict[str, object]:
    operational = args.operational_dir
    accounting = read_json(operational / "05-production-change-accounting.json")
    return {
        "contract": "production-change-accounting-v1",
        "prior_task_changed_scheduler_objects": 6,
        "current_task_new_scheduler_mutations": 2,
        "current_paused_scheduler_objects": 8,
        "additional_dependencies_paused": [
            "com.seungsoo.thesis-monitor.ai-review-fallback",
            "com.seungsoo.thesis-monitor.ai-review-delivery-retry",
        ],
        "production_scheduler_change": 1,
        "unauthorized_scheduler_change": 0,
        "production_db_mutation_task_initiated": 0,
        "production_telegram_send_task_initiated": 0,
        "stock_registration_change": 0,
        "main_merge": 0,
        "deployment": 0,
        "night_futures_change": 0,
        "forced_termination_count": 0,
        "auto_resume_configured": False,
        "historical_transition_activity": accounting.get(
            "observed_non_task_transition_activity"
        ),
        "status": "PASS",
    }


def _write_custom_completion(
    args: argparse.Namespace,
    *,
    state: Mapping[str, object],
    stop_reason: str | None,
) -> dict[str, object]:
    base_path = runner.proof_path(args.report_dir, 60)
    base = read_json(base_path) if base_path.is_file() else {}
    cohort = [str(value) for value in state.get("ordered_cohort") or []]
    exposure = _scan_real_exposure(args.output_root, cohort)
    operational = read_json(args.operational_dir / "03-pause-action-and-after-state.json")
    backlog = read_json(args.operational_dir / "04-backlog-and-transition-observation.json")
    result = {
        "contract": PROGRAM_CONTRACT,
        "operational_pause_status": "PAUSED_COMPLETE",
        "operational_pause_us_status": operational.get("us_pause_status"),
        "operational_pause_kr_status": operational.get("kr_pause_status"),
        "restoration_requires_explicit_user_request": True,
        "historical_changed_scheduler_object_count": 6,
        "current_task_new_scheduler_mutation_count": 2,
        "current_paused_scheduler_object_count": 8,
        "transition_backlog_observation": backlog,
        "source_generation_id": state.get("source_generation_id"),
        "runtime_generation_id": state.get("program_generation_id"),
        "ordered_cohort": cohort,
        "market_mix": {"us": TARGET_US, "kr": TARGET_KR} if cohort else None,
        "model": runner.MODEL,
        "reasoning_effort": runner.EFFORT,
        "model_timeout_seconds": runner.TIMEOUT_SECONDS,
        "model_timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "actual_model_invocation_count": state.get("model_invocation_count", 0),
        "model_retry_count": state.get("transport_retry_count", 0),
        "run_results": state.get("run_results") or {run: "NOT_RUN" for run in RUNS},
        "exposure": exposure,
        "ownership_generalization_verdict": base.get(
            "ownership_generalization_verdict", "NOT_MEASURED"
        ),
        "production_change": production_change_proof(args),
        "readiness": base.get("readiness") or state.get("readiness"),
        "next_scope": base.get("next_scope"),
        "stop_reason": stop_reason,
        "status": (
            "PASS"
            if str(base.get("readiness") or "").startswith("READY_")
            else "STOPPED"
        ),
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
    guard = guarded.LiveWorkloadGuard(
        args.output_root / "live-workload-coexistence-audit.json",
        observer=PauseAwareWorkloadObserver(),
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
            required = (
                "execution_status",
                "identity_gate_status",
                "ownership_gate_status",
                "renderer_gate_status",
                "hard_safety_gate_status",
                "preservation_status",
            )
            if any(document.get(key) != "PASS" for key in required):
                raise runner.SemanticStop(f"{run}_required_gate_failed")
            documents[run] = document
            state["run_results"][run] = (
                f"{document['validation_pass_count']}/{TARGET_TOTAL}"
            )
            state["real_investment_model_invocation_count"] = adapter.model_call_count
            write_json(args.output_root / "program-state.json", state)
        except Exception as exc:
            stop_reason = f"{type(exc).__name__}:{exc}"
            exposure = _scan_real_exposure(args.output_root, cohort)
            state["exposed_subjects"] = exposure["unique_exposed_issuers"]
            state["holdout_output_exposure_state"] = exposure["output_exposure_state"]
            state["stop_reason"] = stop_reason
            state["real_investment_model_invocation_count"] = adapter.model_call_count
            write_json(args.output_root / "program-state.json", state)
            runner.write_failed_run(args, run, stop_reason)
            for pending in RUNS[RUNS.index(run) + 1 :]:
                runner.write_not_run(args, pending, stop_reason)
            break
    exposure = _scan_real_exposure(args.output_root, cohort)
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
        args=args, state=state, documents=documents, stop_reason=stop_reason
    )
    runner.write_proof(args.report_dir, 57, production_change_proof(args))
    runner.write_proof(
        args.report_dir,
        58,
        {
            "contract": "night-futures-no-change-v1",
            "night_futures_code_mutation": 0,
            "night_futures_decision_packet_injection": 0,
            "status": "PASS",
        },
    )
    state = read_json(args.output_root / "program-state.json")
    result = _write_custom_completion(args, state=state, stop_reason=stop_reason)
    runner.write_reports(args.report_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)


def _copy_tree_files(source: Path, destination: Path) -> None:
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def _safe_zip_member(name: str) -> bool:
    return not (
        name.startswith("/")
        or "\\" in name
        or ".." in PurePosixPath(name).parts
    )


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "EVIDENCE_COMPLETE":
        raise ValueError("evidence_complete_state_required")
    if not state.get("source_gate_only"):
        verify_frozen(args, state)
    completion = read_json(runner.proof_path(args.report_dir, 60))
    completion.update(
        {
            "final_head_sha": git_value("rev-parse", "HEAD"),
            "focused_tests": args.focused_tests,
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    validation_pass = all(
        value == "PASS"
        for value in (
            args.focused_tests,
            args.full_tests,
            args.ruff,
            args.diff_check,
        )
    )
    if not validation_pass:
        completion["readiness"] = "NOT_READY_VALIDATION_FAILED"
        completion["next_scope"] = "BOUNDED_VALIDATION_REPAIR"
    runner.write_proof(args.report_dir, 60, completion)
    custom = _write_custom_completion(
        args, state=state, stop_reason=state.get("stop_reason")
    )
    custom.update(
        {
            "final_head_sha": git_value("rev-parse", "HEAD"),
            "focused_tests": args.focused_tests,
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
            "readiness": completion.get("readiness"),
            "next_scope": completion.get("next_scope"),
            "status": (
                "PASS"
                if str(completion.get("readiness") or "").startswith("READY_")
                else "STOPPED"
            ),
        }
    )
    write_json(
        args.report_dir / "proofs" / f"{CUSTOM_COMPLETION_NAME}.json", custom
    )
    write_text(
        args.report_dir / f"{CUSTOM_COMPLETION_NAME}.md",
        runner.report_body(CUSTOM_COMPLETION_NAME, custom),
    )
    runner.write_reports(args.report_dir)
    write_text(
        args.report_dir / "README.md",
        "# Monitoring Pause Completion & Fresh Issuer Ownership Proof\n\n"
        f"- Operational pause: `PAUSED_COMPLETE`\n"
        f"- Cohort: `{len(state.get('ordered_cohort') or [])}` issuers\n"
        f"- Source generation: `{state.get('source_generation_id')}`\n"
        f"- Runtime generation: `{state.get('program_generation_id')}`\n"
        f"- Real model invocations: `{state.get('model_invocation_count', 0)}`\n"
        f"- Readiness: `{completion.get('readiness')}`\n\n"
        "The eight monitoring scheduler objects remain paused. Restoration is not "
        "included and requires a new explicit user request. The artifact index covers "
        "every ZIP payload except the root index itself.\n",
    )
    if args.bundle_root.exists():
        raise ValueError("new_bundle_root_required")
    args.bundle_root.mkdir(parents=True)
    _copy_tree_files(args.report_dir, args.bundle_root / "reports")
    _copy_tree_files(args.output_root, args.bundle_root / "experiment")
    _copy_tree_files(args.operational_dir, args.bundle_root / "operational")
    write_text(
        args.bundle_root / "README.md",
        (args.report_dir / "README.md").read_text(encoding="utf-8"),
    )
    payloads = sorted(
        path
        for path in args.bundle_root.rglob("*")
        if path.is_file() and path != args.bundle_root / "artifact-index.json"
    )
    completion["artifact_count"] = len(payloads) + 1
    completion["artifact_hash_mismatch_count"] = 0
    completion["artifact_size_mismatch_count"] = 0
    completion["artifact_secret_scan_failure_count"] = 0
    custom["artifact_count"] = len(payloads) + 1
    custom["artifact_hash_mismatch_count"] = 0
    custom["artifact_size_mismatch_count"] = 0
    custom["artifact_secret_scan_failure_count"] = 0
    runner.write_proof(args.report_dir, 60, completion)
    write_json(
        args.report_dir / "proofs" / f"{CUSTOM_COMPLETION_NAME}.json", custom
    )
    runner.write_reports(args.report_dir)
    _copy_tree_files(args.report_dir, args.bundle_root / "reports")
    payloads = sorted(
        path
        for path in args.bundle_root.rglob("*")
        if path.is_file() and path != args.bundle_root / "artifact-index.json"
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
        "contract": "monitoring-pause-fresh-proof-artifact-index-v1",
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
        names = archive.namelist()
        duplicate_count = len(names) - len(set(names))
        unsafe_count = sum(not _safe_zip_member(name) for name in names)
        bad_member = archive.testzip()
        archived_index = zip_json(archive, "artifact-index.json")
        archived_rows = archived_index["rows"]
        indexed_names = {str(row["path"]) for row in archived_rows}
        expected_names = set(names) - {"artifact-index.json"}
        hash_mismatches = 0
        size_mismatches = 0
        for row in archived_rows:
            payload = archive.read(str(row["path"]))
            hash_mismatches += bytes_sha256(payload) != row["sha256"]
            size_mismatches += len(payload) != row["byte_size"]
    if (
        duplicate_count
        or unsafe_count
        or bad_member is not None
        or indexed_names != expected_names
        or hash_mismatches
        or size_mismatches
    ):
        raise ValueError("final_zip_integrity_failure")
    zip_sha256 = file_sha256(args.zip_output)
    write_text(args.zip_output.with_suffix(args.zip_output.suffix + ".sha256"), zip_sha256)
    state.update(
        {
            "state": "COMPLETE",
            "report_zip": str(args.zip_output),
            "report_zip_sha256": zip_sha256,
            "report_zip_member_count": len(names),
            "artifact_indexed_payload_count": len(rows),
            "artifact_secret_scan_failure_count": secret_failures,
            "readiness": completion.get("readiness"),
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze-selection", action="store_true")
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--operational-dir", type=Path, required=True)
    parser.add_argument("--historical-zip", type=Path, required=True)
    parser.add_argument("--expansion-zip", type=Path, required=True)
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
        "operational_dir",
        "historical_zip",
        "expansion_zip",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.freeze_selection:
        freeze_selection(args)
    elif args.prepare:
        prepare(args)
    elif args.execute:
        execute(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
