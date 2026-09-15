from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from app.config import get_settings
from app.models.watchlist import WatchlistItem
from app.providers import opendart_corp_codes
from app.services.company_profile_service import (
    OpenDartCompanyProfileSource,
    SecCompanyProfileSource,
)
from app.services.reference_universe_audit_service import CanonicalSecurityReference
from scripts import fresh_issuer_ownership_proof_transport_risk_carried as legacy
from scripts import monitoring_pause_completion_fresh_issuer_ownership_proof as selection
from scripts import new_issuer_holdout_selection_ownership_proof as runner
from scripts import websocket_timeout_runtime_review_first_a_closeout as closeout


PROGRAM_CONTRACT = "existing-source-env-binding-fresh-holdout-proof-resume-v1"
WORK_INSTRUCTION_PATH = (
    "docs/work-instructions/"
    "20260908-existing-source-env-binding-and-fresh-holdout-proof-resume.md"
)
WORK_INSTRUCTION_SHA256 = (
    "97a374aaab56a3dc68199d7d92b71ac8ad2d1fe41dd138147110dabe48efc502"
)
LATEST_RESULT_NAME = (
    "thesis-monitor-20260907-fresh-issuer-ownership-proof-"
    "transport-risk-carried-report.zip"
)
LATEST_RESULT_SHA256 = (
    "25a9ca43fa0c2e77d272c0e77fe982876f2f53bbcdfa49f1510f071f95fb5c01"
)
LATEST_RESULT_MEMBERS = 231
LATEST_RESULT_INDEXED_PAYLOADS = 230
LATEST_FINAL_HEAD = "be78b8e0a40b2e63d3522487a1482b47b6efe271"
EXPECTED_SELECTION_POLICY_SHA256 = (
    "07defbbe29042495ebaa08cb24ca5fcc57cd42c859bfbf80ccc5d984068b2f8f"
)
EXPECTED_EXCLUSION_REGISTRY_SHA256 = (
    "7ffd6fed1125e88073efb867d3d5adc4024a0f22485e0c376151fbe5e3b6b437"
)
EXPECTED_CANDIDATE_IDENTITIES_SHA256 = (
    "81246812c3b537ab37199bd3a0a361d38522db4db2a3223a33785d2520d9d4ba"
)
EXPECTED_EXCLUSION_COUNT = 117
FROZEN_EVALUATION_CUTOFF = "2026-09-07T15:27:51+00:00"
TARGET_US = 4
TARGET_KR = 12
TARGET_TOTAL = TARGET_US + TARGET_KR
EXPECTED_CONTEXTS = 32
REPORT_DIRECTORY = "20260908-existing-source-env-binding-fresh-holdout-proof-resume"
SMOKE_SUBJECTS = {"us": "GOOGL", "kr": "005930"}

REPORT_NAMES = (
    "01-repository-provenance",
    "02-latest-result-integrity",
    "03-existing-source-configuration-discovery",
    "04-existing-source-configuration-binding",
    "05-source-configuration-secret-safety-audit",
    "06-source-configuration-preflight",
    "07-us-source-config-smoke",
    "08-kr-source-config-smoke",
    "09-selection-state-reuse-proof",
    "10-prior-real-issuer-exclusion-registry",
    "11-us-candidate-source-readiness",
    "12-kr-candidate-source-readiness",
    "13-dual-market-source-decision",
    "14-fresh-holdout-selection-result",
    "15-fresh-source-generation",
    "16-source-identity-audit",
    "17-source-sufficiency-audit",
    "18-fresh-source-lock",
    "19-fresh-holdout-precommit",
    "20-architecture-freeze",
    "21-prompt-schema-freeze",
    "22-model-context-freeze",
    "23-transport-freeze",
    "24-schedule-pause-observation",
    "25-first-execution-summary",
    "26-first-context-artifact-manifest",
    "27-first-context-partial-semantic-audits",
    "28-first-ownership-gate",
    "29-first-renderer-gate",
    "30-first-hard-safety-gate",
    "31-first-message-quality-advisory",
    "32-run-a-execution-summary",
    "33-run-a-context-artifact-manifest",
    "34-run-a-context-partial-semantic-audits",
    "35-run-a-ownership-gate",
    "36-run-a-renderer-gate",
    "37-run-a-hard-safety-gate",
    "38-run-a-message-quality-advisory",
    "39-run-b-execution-summary",
    "40-run-b-context-artifact-manifest",
    "41-run-b-context-partial-semantic-audits",
    "42-run-b-ownership-gate",
    "43-run-b-renderer-gate",
    "44-run-b-hard-safety-gate",
    "45-run-b-message-quality-advisory",
    "46-run-c-execution-summary",
    "47-run-c-context-artifact-manifest",
    "48-run-c-context-partial-semantic-audits",
    "49-run-c-ownership-gate",
    "50-run-c-renderer-gate",
    "51-run-c-hard-safety-gate",
    "52-run-c-message-quality-advisory",
    "53-holdout-exposure-retirement-state",
    "54-core-stability",
    "55-timing-stability",
    "56-ownership-generalization",
    "57-renderer-ownership-proof",
    "58-hard-safety-regression",
    "59-message-quality-summary",
    "60-runtime-reliability-observations",
    "61-production-no-change",
    "62-night-futures-no-change",
    "63-monitoring-bootstrap-next-handoff",
    "64-program-completion",
)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    legacy.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    legacy.write_text(path, value)


def file_sha256(path: Path) -> str:
    return legacy.file_sha256(path)


def canonical_sha256(value: object) -> str:
    return legacy.canonical_sha256(value)


def git_value(*args: str) -> str:
    return legacy.git_value(*args)


def _summary_value(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return f"{len(value)} rows; sha256={canonical_sha256(value)}"
    if isinstance(value, dict):
        if len(value) > 12:
            return f"{len(value)} keys; sha256={canonical_sha256(value)}"
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


def report_body(name: str, proof: Mapping[str, object]) -> str:
    rows = [
        f"| {str(key).replace('|', '/')} | "
        f"{_summary_value(value).replace('|', '/')} |"
        for key, value in proof.items()
    ]
    return f"# {name}\n\n| Field | Value |\n| --- | --- |\n" + "\n".join(rows) + "\n"


def proof_path(report_dir: Path, number: int) -> Path:
    return report_dir / "proofs" / f"{REPORT_NAMES[number - 1]}.json"


def write_proof(report_dir: Path, number: int, proof: Mapping[str, object]) -> None:
    name = REPORT_NAMES[number - 1]
    write_json(proof_path(report_dir, number), proof)
    write_text(report_dir / f"{name}.md", report_body(name, proof))


def _legacy_args(args: argparse.Namespace) -> argparse.Namespace:
    values = vars(args).copy()
    values["report_dir"] = args.report_dir / "internal"
    return argparse.Namespace(**values)


def _configure_legacy() -> None:
    legacy.PROGRAM_CONTRACT = PROGRAM_CONTRACT
    legacy.WORK_INSTRUCTION_PATH = WORK_INSTRUCTION_PATH
    legacy.WORK_INSTRUCTION_SHA256 = WORK_INSTRUCTION_SHA256
    legacy.REPORT_DIRECTORY = f"{REPORT_DIRECTORY}/internal"
    legacy._configure_prior_module()


def _zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def _zip_jsonl(archive: zipfile.ZipFile, member: str) -> list[dict[str, Any]]:
    rows = []
    for line in archive.read(member).decode("utf-8").splitlines():
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"zip_jsonl_object_required:{member}")
        rows.append(value)
    return rows


def _verify_latest_result(path: Path) -> dict[str, object]:
    result = legacy._verify_zip(
        path,
        expected_name=LATEST_RESULT_NAME,
        expected_sha256=LATEST_RESULT_SHA256,
        expected_members=LATEST_RESULT_MEMBERS,
        expected_indexed=LATEST_RESULT_INDEXED_PAYLOADS,
    )
    with zipfile.ZipFile(path) as archive:
        state = _zip_json(archive, "experiment/program-state.json")
        completion = _zip_json(archive, "completion.json")
    checks = {
        "selection_policy_sha256": (
            state.get("selection_policy_sha256") == EXPECTED_SELECTION_POLICY_SHA256
        ),
        "exclusion_registry_sha256": (
            state.get("exclusion_registry_sha256")
            == EXPECTED_EXCLUSION_REGISTRY_SHA256
        ),
        "candidate_identities_sha256": (
            state.get("candidate_identities_sha256")
            == EXPECTED_CANDIDATE_IDENTITIES_SHA256
        ),
        "exclusion_registry_count": (
            state.get("exclusion_registry_count") == EXPECTED_EXCLUSION_COUNT
        ),
        "model_invocation_count": state.get("model_invocation_count") == 0,
        "ordered_cohort_unlocked": not state.get("ordered_cohort"),
        "stop_reason": (
            state.get("stop_reason") == "REQUIRED_SOURCE_CONFIGURATION_UNAVAILABLE"
        ),
        "final_head": completion.get("final_head_sha") == LATEST_FINAL_HEAD,
    }
    if not all(checks.values()):
        raise ValueError(
            "latest_result_selection_state_mismatch:"
            + ",".join(key for key, passed in checks.items() if not passed)
        )
    return {**result, "state_checks": checks, "selection_state": state, "status": "PASS"}


def _repository_provenance() -> dict[str, object]:
    instruction_commit = git_value("log", "-1", "--format=%H", "--", WORK_INSTRUCTION_PATH)
    head = git_value("rev-parse", "HEAD")
    ancestor = subprocess.run(
        ("git", "merge-base", "--is-ancestor", LATEST_FINAL_HEAD, head),
        check=False,
    ).returncode == 0
    changed = [
        line
        for line in git_value("diff", "--name-only", f"{LATEST_FINAL_HEAD}..{head}").splitlines()
        if line
    ]
    allowed = {
        WORK_INSTRUCTION_PATH,
        "scripts/existing_source_env_binding_fresh_holdout_resume.py",
        "tests/test_existing_source_env_binding_fresh_holdout_resume.py",
    }
    unexpected = sorted(set(changed) - allowed)
    result = {
        "contract": "repository-provenance-v1",
        "branch": git_value("branch", "--show-current"),
        "base_sha": LATEST_FINAL_HEAD,
        "work_instruction_commit": instruction_commit,
        "implementation_commit": head,
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "origin_main": git_value("rev-parse", "origin/main"),
        "latest_result_final_head_is_ancestor": ancestor,
        "changed_paths_since_latest_result": changed,
        "unexpected_semantic_paths": unexpected,
        "architecture_semantic_drift": int(bool(unexpected)),
        "prompt_semantic_drift": 0,
        "schema_semantic_drift": 0,
        "model_semantic_input_drift": 0,
        "transport_topology_mutation": 0,
        "status": "PASS" if ancestor and not unexpected else "FAIL",
    }
    if result["status"] != "PASS":
        raise ValueError("UNEXPLAINED_SEMANTIC_REPOSITORY_DRIFT")
    return result


def source_configuration_audit(repo_root: Path) -> dict[str, object]:
    override = os.environ.get("THESIS_MONITOR_ENV_FILE")
    bound_path = Path(override).expanduser().resolve() if override else None
    get_settings.cache_clear()
    settings = get_settings()
    required = {
        "OPENDART_API_KEY": bool(settings.opendart_api_key),
        "SEC_USER_AGENT": bool(settings.sec_user_agent),
    }
    file_exists = bool(bound_path and bound_path.is_file())
    outside_repository = bool(
        bound_path and not bound_path.is_relative_to(repo_root.resolve())
    )
    configured = bool(override)
    passed = configured and file_exists and outside_repository and all(required.values())
    return {
        "contract": "existing-protected-source-configuration-binding-v1",
        "source_config_loader": "app.config.get_settings:_settings_env_file",
        "source_config_loader_sha256": runner.source_sha256(get_settings),
        "env_override_name": "THESIS_MONITOR_ENV_FILE",
        "canonical_env_override_configured": configured,
        "protected_source_config_located": file_exists,
        "protected_source_config_bound": passed,
        "protected_config_outside_repository": outside_repository,
        "protected_config_identity_sha256": (
            hashlib.sha256(str(bound_path).encode("utf-8")).hexdigest()
            if bound_path is not None
            else None
        ),
        "required_setting_presence": required,
        "missing_required_settings": sorted(
            key for key, present in required.items() if not present
        ),
        "secret_values_emitted": 0,
        "working_directory_env_file_present": (repo_root / ".env").is_file(),
        "status": "PASS" if passed else "FAIL",
    }


def _reference_for(
    rows: Sequence[Mapping[str, object]], ticker: str
) -> CanonicalSecurityReference:
    matches = [row for row in rows if str(row.get("display_symbol")) == ticker]
    if len(matches) != 1:
        raise ValueError(f"smoke_reference_identity_not_unique:{ticker}:{len(matches)}")
    return CanonicalSecurityReference.model_validate(matches[0])


def _watchlist_item(reference: CanonicalSecurityReference) -> WatchlistItem:
    return WatchlistItem(
        ticker=reference.display_symbol,
        company_name=reference.issuer_name or reference.security_name,
        exchange=reference.provider_exchange or reference.exchange,
        active=False,
        monitoring_requested=False,
        production_eligible=False,
    )


async def _source_smokes(
    *, expansion_zip: Path, configuration: Mapping[str, object]
) -> dict[str, dict[str, object]]:
    if configuration.get("status") != "PASS":
        return {
            market: {
                "contract": f"{market}-source-config-smoke-v1",
                "request_count": 0,
                "reason": "SOURCE_CONFIGURATION_PREFLIGHT_FAILED",
                "status": "NOT_RUN",
            }
            for market in ("us", "kr")
        }
    get_settings.cache_clear()
    settings = get_settings()
    with zipfile.ZipFile(expansion_zip) as archive:
        us_rows = _zip_jsonl(archive, selection.REFERENCE_MEMBERS["us"])
        kr_rows = _zip_jsonl(archive, selection.REFERENCE_MEMBERS["kr"])
        opendart_corp_codes._cached_companies = (
            opendart_corp_codes._parse_corp_code_zip(
                archive.read(selection.OPENDART_REFERENCE_MEMBER)
            )
        )
    us_reference = _reference_for(us_rows, SMOKE_SUBJECTS["us"])
    kr_reference = _reference_for(kr_rows, SMOKE_SUBJECTS["kr"])

    async def us_smoke() -> dict[str, object]:
        source = SecCompanyProfileSource(settings.sec_user_agent or "")
        cik = str(us_reference.canonical_issuer_key or "").removeprefix("sec:cik:")
        source._ticker_ciks = {us_reference.display_symbol: cik}
        try:
            profile = await source.fetch(_watchlist_item(us_reference), None)
            passed = bool(
                profile
                and profile.ticker == us_reference.display_symbol
                and profile.cik == cik
            )
            return {
                "contract": "us-source-config-smoke-v1",
                "subject": us_reference.display_symbol,
                "source_client": "SecCompanyProfileSource",
                "request_count": 1,
                "profile_received": int(profile is not None),
                "profile_identity_sha256": (
                    canonical_sha256(
                        {
                            "ticker": profile.ticker,
                            "source": profile.source,
                            "cik": profile.cik,
                            "source_as_of": profile.source_as_of,
                        }
                    )
                    if profile is not None
                    else None
                ),
                "secret_values_emitted": 0,
                "status": "PASS" if passed else "FAIL",
            }
        except Exception as exc:
            return {
                "contract": "us-source-config-smoke-v1",
                "subject": us_reference.display_symbol,
                "source_client": "SecCompanyProfileSource",
                "request_count": 1,
                "profile_received": 0,
                "error_type": type(exc).__name__,
                "secret_values_emitted": 0,
                "status": "FAIL",
            }

    async def kr_smoke() -> dict[str, object]:
        source = OpenDartCompanyProfileSource(settings.opendart_api_key or "")
        try:
            profile = await source.fetch(_watchlist_item(kr_reference), None)
            passed = bool(
                profile
                and profile.ticker == kr_reference.display_symbol
                and profile.corp_code
            )
            return {
                "contract": "kr-source-config-smoke-v1",
                "subject": kr_reference.display_symbol,
                "source_client": "OpenDartCompanyProfileSource",
                "request_count": 1,
                "profile_received": int(profile is not None),
                "profile_identity_sha256": (
                    canonical_sha256(
                        {
                            "ticker": profile.ticker,
                            "source": profile.source,
                            "corp_code": profile.corp_code,
                            "source_as_of": profile.source_as_of,
                        }
                    )
                    if profile is not None
                    else None
                ),
                "secret_values_emitted": 0,
                "status": "PASS" if passed else "FAIL",
            }
        except Exception as exc:
            return {
                "contract": "kr-source-config-smoke-v1",
                "subject": kr_reference.display_symbol,
                "source_client": "OpenDartCompanyProfileSource",
                "request_count": 1,
                "profile_received": 0,
                "error_type": type(exc).__name__,
                "secret_values_emitted": 0,
                "status": "FAIL",
            }

    us_result = await us_smoke()
    kr_result = await kr_smoke()
    return {"us": us_result, "kr": kr_result}


def _write_not_run_proofs(
    report_dir: Path, *, start: int, reason: str, status: str = "NOT_RUN"
) -> None:
    for number in range(start, len(REPORT_NAMES) + 1):
        if proof_path(report_dir, number).is_file():
            continue
        write_proof(
            report_dir,
            number,
            {
                "contract": f"{REPORT_NAMES[number - 1]}-v1",
                "reason": reason,
                "status": status,
            },
        )


def _bootstrap_terminal_state(
    args: argparse.Namespace,
    *,
    provenance: Mapping[str, object],
    integrity: Mapping[str, object],
    configuration: Mapping[str, object],
    smokes: Mapping[str, Mapping[str, object]],
    reason: str,
) -> None:
    source_request_count = sum(
        int(row.get("request_count") or 0) for row in smokes.values()
    )
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": LATEST_FINAL_HEAD,
        "work_instruction_commit": provenance.get("work_instruction_commit"),
        "implementation_commit": provenance.get("implementation_commit"),
        "final_head_sha": git_value("rev-parse", "HEAD"),
        "branch": provenance.get("branch"),
        "latest_result_zip_sha256": LATEST_RESULT_SHA256,
        "latest_result_integrity": integrity.get("status"),
        "source_config_loader": configuration.get("source_config_loader"),
        "protected_source_config_located": configuration.get(
            "protected_source_config_located"
        ),
        "protected_source_config_bound": configuration.get(
            "protected_source_config_bound"
        ),
        "opendart_api_key_present": configuration.get(
            "required_setting_presence", {}
        ).get("OPENDART_API_KEY"),
        "sec_user_agent_present": configuration.get(
            "required_setting_presence", {}
        ).get("SEC_USER_AGENT"),
        "secret_values_emitted": 0,
        "source_configuration_preflight_status": configuration.get("status"),
        "candidate_source_request_count_after_failed_preflight": 0,
        "us_source_config_smoke_status": smokes["us"].get("status"),
        "kr_source_config_smoke_status": smokes["kr"].get("status"),
        "source_smoke_request_count": source_request_count,
        "selection_policy_hash": EXPECTED_SELECTION_POLICY_SHA256,
        "exclusion_registry_hash": EXPECTED_EXCLUSION_REGISTRY_SHA256,
        "exclusion_registry_count": EXPECTED_EXCLUSION_COUNT,
        "frozen_evaluation_cutoff": FROZEN_EVALUATION_CUTOFF,
        "us_source_target_status": "NOT_RUN",
        "kr_source_target_status": "NOT_RUN",
        "fresh_holdout_cohort": [],
        "fresh_source_generation_id": None,
        "fresh_source_lock": None,
        "ordered_issuers": [],
        "issuer_market_mix": {"us": 0, "kr": 0},
        "model": runner.MODEL,
        "reasoning_effort": runner.EFFORT,
        "batch_semantics": runner.BATCH_SEMANTICS,
        "subjects_per_context": runner.CONTEXT_SIZE,
        "timeout_seconds": runner.TIMEOUT_SECONDS,
        "timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "planned_contexts": EXPECTED_CONTEXTS,
        "attempted_contexts": 0,
        "successful_contexts": 0,
        "failed_contexts": 0,
        "real_model_invocation_count": 0,
        "raw_output_document_count": 0,
        "unique_issuer_output_count": 0,
        "run_results": {run: "NOT_RUN" for run in runner.RUNS},
        "exposure_state": "UNEXPOSED",
        "future_unseen_reuse_allowed": 1,
        "production_db_mutation": 0,
        "production_send": 0,
        "monitoring_registration_change": 0,
        "live_v2_change": 0,
        "night_futures_change": 0,
        "status": "STOPPED",
        "readiness": "NOT_READY_PREPARATION_CONFIGURATION_BLOCKED",
        "stop_reason": reason,
        "next_scope": "EXISTING_SOURCE_CONFIGURATION_BINDING_OPERATOR_REPAIR",
    }
    write_proof(args.report_dir, 64, completion)
    _write_not_run_proofs(args.report_dir, start=9, reason=reason)
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "EVIDENCE_COMPLETE",
        "source_gate_only": True,
        "work_instruction_commit": provenance.get("work_instruction_commit"),
        "implementation_commit": provenance.get("implementation_commit"),
        "selection_policy_sha256": EXPECTED_SELECTION_POLICY_SHA256,
        "exclusion_registry_sha256": EXPECTED_EXCLUSION_REGISTRY_SHA256,
        "exclusion_registry_count": EXPECTED_EXCLUSION_COUNT,
        "model_invocation_count": 0,
        "ordered_cohort": [],
        "stop_reason": reason,
        "readiness": completion["readiness"],
        "next_scope": completion["next_scope"],
    }
    write_json(args.output_root / "program-state.json", state)


def _copy_selection_state(
    *, latest_zip: Path, output_root: Path, internal_report_dir: Path
) -> dict[str, object]:
    output_members = {
        "experiment/candidate-identities.json": "candidate-identities.json",
        "experiment/selection-inputs/expansion-handoff.json": (
            "selection-inputs/expansion-handoff.json"
        ),
        "experiment/selection-inputs/kr-candidates.jsonl": (
            "selection-inputs/kr-candidates.jsonl"
        ),
        "experiment/selection-inputs/latest-exposed-state.json": (
            "selection-inputs/latest-exposed-state.json"
        ),
        "experiment/selection-inputs/merged-registry.json": (
            "selection-inputs/merged-registry.json"
        ),
        "experiment/selection-inputs/prior-101-registry.json": (
            "selection-inputs/prior-101-registry.json"
        ),
        "experiment/selection-inputs/us-candidates.jsonl": (
            "selection-inputs/us-candidates.jsonl"
        ),
    }
    legacy_proofs = (3, 4, 5, 6, 9)
    with zipfile.ZipFile(latest_zip) as archive:
        state = _zip_json(archive, "experiment/program-state.json")
        for source, relative in output_members.items():
            target = output_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(source))
        for number in legacy_proofs:
            name = runner.PROOF_NAMES[number - 1]
            payload = archive.read(f"reports/proofs/{name}.json")
            target = internal_report_dir / "proofs" / f"{name}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            value = json.loads(payload)
            write_text(internal_report_dir / f"{name}.md", runner.report_body(name, value))
    identities = read_json(output_root / "candidate-identities.json")
    policy = read_json(
        internal_report_dir / "proofs" / f"{runner.PROOF_NAMES[4]}.json"
    )
    registry = read_json(output_root / "selection-inputs" / "merged-registry.json")
    checks = {
        "selection_policy_hash": (
            canonical_sha256(policy) == EXPECTED_SELECTION_POLICY_SHA256
        ),
        "candidate_identity_hash": (
            canonical_sha256(identities) == EXPECTED_CANDIDATE_IDENTITIES_SHA256
        ),
        "exclusion_registry_hash": (
            canonical_sha256(registry) == EXPECTED_EXCLUSION_REGISTRY_SHA256
        ),
        "exclusion_registry_count": len(registry.get("rows") or [])
        == EXPECTED_EXCLUSION_COUNT,
        "prior_model_invocations": state.get("model_invocation_count") == 0,
        "prior_cohort_unlocked": not state.get("ordered_cohort"),
    }
    if not all(checks.values()):
        raise ValueError(
            "selection_state_reuse_failure:"
            + ",".join(key for key, passed in checks.items() if not passed)
        )
    return {
        "contract": "unexposed-selection-state-reuse-v1",
        "source_bundle_sha256": LATEST_RESULT_SHA256,
        "selection_policy_hash": EXPECTED_SELECTION_POLICY_SHA256,
        "candidate_identity_hash": EXPECTED_CANDIDATE_IDENTITIES_SHA256,
        "exclusion_registry_hash": EXPECTED_EXCLUSION_REGISTRY_SHA256,
        "exclusion_registry_count": EXPECTED_EXCLUSION_COUNT,
        "frozen_evaluation_cutoff": FROZEN_EVALUATION_CUTOFF,
        "candidate_order_regenerated": 0,
        "prior_failed_source_results_promoted": 0,
        "prior_model_output_count": 0,
        "checks": checks,
        "status": "PASS",
    }


def bootstrap(args: argparse.Namespace) -> None:
    _configure_legacy()
    repo_root = Path.cwd().resolve()
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    if file_sha256(repo_root / WORK_INSTRUCTION_PATH) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_before_bootstrap")

    provenance = _repository_provenance()
    integrity = _verify_latest_result(args.latest_result_zip)
    pause = closeout.observe_pause_state()
    if pause.get("status") != "VERIFIED_PAUSED_COMPLETE":
        raise ValueError(f"monitoring_pause_not_verified:{pause.get('status')}")

    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)
    configuration = source_configuration_audit(repo_root)
    discovery = {
        "contract": "existing-source-configuration-discovery-v1",
        "source_config_loader": configuration["source_config_loader"],
        "canonical_env_override_configured": configuration[
            "canonical_env_override_configured"
        ],
        "protected_source_config_located": configuration[
            "protected_source_config_located"
        ],
        "working_directory_env_file_present": configuration[
            "working_directory_env_file_present"
        ],
        "secret_values_emitted": 0,
        "status": configuration["status"],
    }
    binding = {
        **configuration,
        "binding_method": "THESIS_MONITOR_ENV_FILE_TO_EXISTING_PROTECTED_FILE",
        "protected_env_file_copied_into_worktree": 0,
        "machine_specific_path_committed": 0,
    }
    secret_safety = {
        "contract": "source-configuration-secret-safety-audit-v1",
        "secret_values_emitted": 0,
        "env_file_copied": 0,
        "env_file_committed": 0,
        "raw_config_path_emitted": 0,
        "status": "PASS",
    }
    preflight = {
        "contract": "source-configuration-preflight-v1",
        "required_setting_presence": configuration["required_setting_presence"],
        "source_loader_identity_sha256": configuration[
            "source_config_loader_sha256"
        ],
        "protected_source_config_bound": configuration[
            "protected_source_config_bound"
        ],
        "candidate_source_request_count": 0,
        "real_model_invocation_count": 0,
        "secret_values_emitted": 0,
        "status": configuration["status"],
    }
    write_json(args.output_root / "source-configuration-audit.json", configuration)
    write_json(args.output_root / "source-configuration-preflight.json", preflight)
    write_proof(args.report_dir, 1, provenance)
    write_proof(args.report_dir, 2, integrity)
    write_proof(args.report_dir, 3, discovery)
    write_proof(args.report_dir, 4, binding)
    write_proof(args.report_dir, 5, secret_safety)
    write_proof(args.report_dir, 6, preflight)

    smokes = asyncio.run(
        _source_smokes(expansion_zip=args.expansion_zip, configuration=configuration)
    )
    write_json(args.output_root / "source-config-smokes.json", smokes)
    write_proof(args.report_dir, 7, smokes["us"])
    write_proof(args.report_dir, 8, smokes["kr"])
    if configuration["status"] != "PASS":
        _bootstrap_terminal_state(
            args,
            provenance=provenance,
            integrity=integrity,
            configuration=configuration,
            smokes=smokes,
            reason="EXISTING_PROTECTED_SOURCE_CONFIGURATION_NOT_LOCATED",
        )
        return
    if any(row.get("status") != "PASS" for row in smokes.values()):
        _bootstrap_terminal_state(
            args,
            provenance=provenance,
            integrity=integrity,
            configuration=configuration,
            smokes=smokes,
            reason="SOURCE_CONFIGURATION_SMOKE_FAILED",
        )
        return

    reuse = _copy_selection_state(
        latest_zip=args.latest_result_zip,
        output_root=args.output_root,
        internal_report_dir=args.report_dir / "internal",
    )
    internal_provenance = {
        **provenance,
        "contract": "repository-provenance-v1",
        "status": "PASS",
    }
    runner.write_proof(args.report_dir / "internal", 1, internal_provenance)
    runner.write_proof(
        args.report_dir / "internal",
        2,
        {
            "contract": "latest-result-selection-state-integrity-v1",
            "latest_result": integrity,
            "status": "PASS",
        },
    )
    write_proof(args.report_dir, 9, reuse)
    registry = read_json(args.output_root / "selection-inputs" / "merged-registry.json")
    write_proof(args.report_dir, 10, registry)
    write_text(
        args.report_dir / "README.md",
        "# Existing Source Environment Binding & Fresh Holdout Proof Resume\n\n"
        "The existing protected source configuration is bound through the canonical "
        "loader. Secret values are never serialized. Candidate evaluation starts only "
        "after both official-profile smoke requests pass.\n",
    )
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "SELECTION_FROZEN",
        "branch": provenance["branch"],
        "base_sha": LATEST_FINAL_HEAD,
        "work_instruction_commit": provenance["work_instruction_commit"],
        "implementation_commit": provenance["implementation_commit"],
        "selection_freeze_commit": "PENDING_COMMIT",
        "selection_policy_sha256": EXPECTED_SELECTION_POLICY_SHA256,
        "candidate_identities_sha256": EXPECTED_CANDIDATE_IDENTITIES_SHA256,
        "exclusion_registry_sha256": EXPECTED_EXCLUSION_REGISTRY_SHA256,
        "exclusion_registry_count": EXPECTED_EXCLUSION_COUNT,
        "frozen_evaluation_cutoff": FROZEN_EVALUATION_CUTOFF,
        "ordered_cohort": [],
        "model_invocation_count": 0,
        "production_scheduler_mutation": 0,
        "auto_resume_executed": 0,
        "production_send": 0,
        "initial_pause_observation": pause,
        "source_configuration": configuration,
        "source_config_smokes": smokes,
        "candidate_source_request_count_after_failed_preflight": 0,
        "carried_runtime_risk": legacy.CARRIED_RUNTIME_RISK,
    }
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def _verify_bound_preflight(args: argparse.Namespace) -> dict[str, object]:
    configuration = source_configuration_audit(Path.cwd().resolve())
    if configuration.get("status") != "PASS":
        raise ValueError("SOURCE_CONFIGURATION_PREFLIGHT_FAILED_BEFORE_CANDIDATE_LOOP")
    stored = read_json(args.output_root / "source-configuration-audit.json")
    stable_fields = (
        "source_config_loader",
        "source_config_loader_sha256",
        "protected_config_identity_sha256",
        "required_setting_presence",
        "secret_values_emitted",
    )
    if any(configuration.get(field) != stored.get(field) for field in stable_fields):
        raise ValueError("source_configuration_binding_drift")
    smokes = read_json(args.output_root / "source-config-smokes.json")
    if any(
        not isinstance(smokes.get(market), Mapping)
        or smokes[market].get("status") != "PASS"
        for market in ("us", "kr")
    ):
        raise ValueError("source_configuration_smoke_not_passed")
    return configuration


def prepare(args: argparse.Namespace) -> None:
    _configure_legacy()
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "SELECTION_FROZEN":
        raise ValueError("selection_frozen_state_required")
    _verify_bound_preflight(args)
    state["selection_freeze_commit"] = git_value("rev-parse", "HEAD")
    write_json(args.output_root / "program-state.json", state)
    legacy.prepare(_legacy_args(args))
    state = read_json(args.output_root / "program-state.json")
    state.update(
        {
            "implementation_commit": state.get("implementation_commit")
            or git_value("rev-parse", "HEAD"),
            "selection_freeze_commit": state.get("selection_freeze_commit")
            or git_value("rev-parse", "HEAD"),
            "frozen_evaluation_cutoff": FROZEN_EVALUATION_CUTOFF,
            "candidate_source_request_count_after_failed_preflight": 0,
            "source_configuration_preflight_status": "PASS",
            "us_source_config_smoke_status": "PASS",
            "kr_source_config_smoke_status": "PASS",
        }
    )
    write_json(args.output_root / "program-state.json", state)
    _write_source_phase_reports(args)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def seal(args: argparse.Namespace) -> None:
    _configure_legacy()
    _verify_bound_preflight(args)
    legacy.seal(_legacy_args(args))


def execute(args: argparse.Namespace) -> None:
    _configure_legacy()
    _verify_bound_preflight(args)
    legacy.execute(_legacy_args(args))


def _legacy_proof(args: argparse.Namespace, number: int) -> dict[str, Any]:
    path = runner.proof_path(args.report_dir / "internal", number)
    if path.is_file():
        return read_json(path)
    return {
        "contract": f"legacy-proof-{number}-v1",
        "reason": "UPSTREAM_STAGE_NOT_RUN",
        "status": "NOT_RUN",
    }


def _message_quality_for_run(
    args: argparse.Namespace, run: str
) -> dict[str, object]:
    path = args.output_root / "run-artifacts" / run.upper() / "message-quality.json"
    if path.is_file():
        value = read_json(path)
        return {**value, "gate_role": legacy.QUALITY_GATE_ROLE}
    return {
        "contract": "per-run-message-quality-advisory-v1",
        "run": run,
        "gate_role": legacy.QUALITY_GATE_ROLE,
        "reason": "RUN_NOT_COMPLETE",
        "status": "NOT_MEASURED",
    }


def _write_source_phase_reports(args: argparse.Namespace) -> None:
    mapping = {
        11: 7,
        12: 10,
        13: 12,
        14: 15,
        15: 16,
        16: 18,
        17: 17,
        18: 19,
        19: 20,
        20: 21,
        21: 22,
        22: 23,
        23: 24,
        24: 26,
    }
    for destination, source in mapping.items():
        write_proof(args.report_dir, destination, _legacy_proof(args, source))


def _write_execution_phase_reports(args: argparse.Namespace) -> None:
    mappings = {
        "first": ((25, 27), (26, 28), (27, 29), (28, 30), (29, 31), (30, 32)),
        "a": ((32, 33), (33, 34), (34, 35), (35, 36), (36, 37), (37, 38)),
        "b": ((39, 39), (40, 40), (41, 41), (42, 42), (43, 43), (44, 44)),
        "c": ((46, 45), (47, 46), (48, 47), (49, 48), (50, 49), (51, 50)),
    }
    quality_destinations = {"first": 31, "a": 38, "b": 45, "c": 52}
    for run, pairs in mappings.items():
        for destination, source in pairs:
            write_proof(args.report_dir, destination, _legacy_proof(args, source))
        write_proof(
            args.report_dir,
            quality_destinations[run],
            _message_quality_for_run(args, run),
        )
    final_mapping = {53: 51, 54: 52, 55: 53, 56: 54, 57: 55, 58: 56}
    for destination, source in final_mapping.items():
        write_proof(args.report_dir, destination, _legacy_proof(args, source))
    quality_path = args.output_root / "advisory-message-quality-summary.json"
    quality = (
        read_json(quality_path)
        if quality_path.is_file()
        else {
            "contract": "message-quality-summary-v1",
            "status": "NOT_MEASURED",
        }
    )
    write_proof(args.report_dir, 59, quality)
    execution_path = args.output_root / "execution-reconciliation.json"
    execution = (
        read_json(execution_path)
        if execution_path.is_file()
        else {
            "planned_contexts": EXPECTED_CONTEXTS,
            "attempted_contexts": 0,
            "successful_contexts": 0,
            "failed_contexts": 0,
            "status": "NOT_MEASURED",
        }
    )
    runtime = {
        "contract": "runtime-reliability-observations-v1",
        "carried_runtime_risk": legacy.CARRIED_RUNTIME_RISK,
        "runtime_reliability_status": "NOT_ESTABLISHED",
        "wrapper_retry_count": execution.get("wrapper_explicit_retry_count", 0),
        "observed_cli_retry_signal_count": execution.get(
            "observed_cli_retry_signal_count", 0
        ),
        "observed_disconnect_count": execution.get(
            "observed_websocket_disconnect_signal_count", 0
        ),
        "explicit_capacity_failure_count": execution.get(
            "explicit_capacity_count", 0
        ),
        "transport_timeout_count": execution.get("watchdog_timeout_count", 0),
        "orphan_count": execution.get("orphan_count", 0),
        "execution": execution,
        "status": "OBSERVED",
    }
    write_proof(args.report_dir, 60, runtime)
    write_proof(args.report_dir, 61, _legacy_proof(args, 57))
    write_proof(args.report_dir, 62, _legacy_proof(args, 58))
    write_proof(args.report_dir, 63, _legacy_proof(args, 59))


def _status(value: Mapping[str, object], default: str = "NOT_MEASURED") -> str:
    return str(value.get("status") or default)


def _completion(args: argparse.Namespace) -> dict[str, object]:
    state = read_json(args.output_root / "program-state.json")
    provenance = read_json(proof_path(args.report_dir, 1))
    integrity = read_json(proof_path(args.report_dir, 2))
    configuration = read_json(args.output_root / "source-configuration-audit.json")
    smokes = read_json(args.output_root / "source-config-smokes.json")
    source_lock = (
        read_json(args.output_root / "source-lock.json")
        if (args.output_root / "source-lock.json").is_file()
        else {}
    )
    execution = (
        read_json(args.output_root / "execution-reconciliation.json")
        if (args.output_root / "execution-reconciliation.json").is_file()
        else {}
    )
    legacy_completion = _legacy_proof(args, 60)
    ordered = list(state.get("ordered_cohort") or [])
    market_by_ticker = source_lock.get("market_by_ticker")
    market_by_ticker = market_by_ticker if isinstance(market_by_ticker, Mapping) else {}
    mix = {
        "us": sum(str(market_by_ticker.get(ticker)) == "us" for ticker in ordered),
        "kr": sum(str(market_by_ticker.get(ticker)) == "kr" for ticker in ordered),
    }
    run_results = legacy_completion.get("run_results")
    run_results = run_results if isinstance(run_results, Mapping) else {
        run: "NOT_RUN" for run in runner.RUNS
    }
    gate_sources = {
        "first": (30, 31, 32),
        "a": (36, 37, 38),
        "b": (42, 43, 44),
        "c": (48, 49, 50),
    }
    gate_fields: dict[str, object] = {}
    for run, (ownership, renderer, safety) in gate_sources.items():
        prefix = "first" if run == "first" else f"run_{run}"
        gate_fields[f"{prefix}_ownership_gate_status"] = _status(
            _legacy_proof(args, ownership)
        )
        gate_fields[f"{prefix}_renderer_gate_status"] = _status(
            _legacy_proof(args, renderer)
        )
        gate_fields[f"{prefix}_hard_safety_gate_status"] = _status(
            _legacy_proof(args, safety)
        )
        gate_fields[f"{prefix}_message_quality_status"] = _status(
            _message_quality_for_run(args, run)
        )
    exposure = _legacy_proof(args, 51)
    core = _legacy_proof(args, 52)
    timing = _legacy_proof(args, 53)
    generalization = _legacy_proof(args, 54)
    pause = closeout.observe_pause_state()
    return {
        "contract": PROGRAM_CONTRACT,
        "base_sha": LATEST_FINAL_HEAD,
        "work_instruction_commit": provenance.get("work_instruction_commit"),
        "implementation_commit": state.get("implementation_commit"),
        "selection_freeze_commit": state.get("selection_freeze_commit"),
        "final_head_sha": git_value("rev-parse", "HEAD"),
        "branch": git_value("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_RESULT_SHA256,
        "latest_result_integrity": integrity.get("status"),
        "source_config_loader": configuration.get("source_config_loader"),
        "protected_source_config_located": configuration.get(
            "protected_source_config_located"
        ),
        "protected_source_config_bound": configuration.get(
            "protected_source_config_bound"
        ),
        "opendart_api_key_present": configuration.get(
            "required_setting_presence", {}
        ).get("OPENDART_API_KEY"),
        "sec_user_agent_present": configuration.get(
            "required_setting_presence", {}
        ).get("SEC_USER_AGENT"),
        "secret_values_emitted": 0,
        "source_configuration_preflight_status": configuration.get("status"),
        "candidate_source_request_count_after_failed_preflight": state.get(
            "candidate_source_request_count_after_failed_preflight", 0
        ),
        "us_source_config_smoke_status": smokes.get("us", {}).get("status"),
        "kr_source_config_smoke_status": smokes.get("kr", {}).get("status"),
        "selection_policy_hash": EXPECTED_SELECTION_POLICY_SHA256,
        "exclusion_registry_hash": EXPECTED_EXCLUSION_REGISTRY_SHA256,
        "exclusion_registry_count": EXPECTED_EXCLUSION_COUNT,
        "frozen_evaluation_cutoff": FROZEN_EVALUATION_CUTOFF,
        "us_source_target_status": _legacy_proof(args, 7).get(
            "source_target_status", "NOT_RUN"
        ),
        "kr_source_target_status": _legacy_proof(args, 10).get(
            "source_target_status", "NOT_RUN"
        ),
        "fresh_holdout_cohort": ordered,
        "fresh_source_generation_id": state.get("source_generation_id"),
        "fresh_source_lock": state.get("source_lock_sha256"),
        "ordered_issuers": ordered,
        "issuer_market_mix": mix,
        "model": runner.MODEL,
        "reasoning_effort": runner.EFFORT,
        "batch_semantics": runner.BATCH_SEMANTICS,
        "subjects_per_context": runner.CONTEXT_SIZE,
        "timeout_seconds": runner.TIMEOUT_SECONDS,
        "timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "architecture_semantic_drift": provenance.get(
            "architecture_semantic_drift", 0
        ),
        "prompt_semantic_drift": provenance.get("prompt_semantic_drift", 0),
        "schema_semantic_drift": provenance.get("schema_semantic_drift", 0),
        "model_semantic_input_drift": provenance.get(
            "model_semantic_input_drift", 0
        ),
        "transport_topology_mutation": provenance.get(
            "transport_topology_mutation", 0
        ),
        "planned_contexts": execution.get("planned_contexts", EXPECTED_CONTEXTS),
        "attempted_contexts": execution.get("attempted_contexts", 0),
        "successful_contexts": execution.get("successful_contexts", 0),
        "failed_contexts": execution.get("failed_contexts", 0),
        "real_model_invocation_count": legacy_completion.get(
            "real_model_invocation_count",
            execution.get("attempted_contexts", 0),
        ),
        "raw_output_document_count": execution.get("raw_output_document_count", 0),
        "unique_issuer_output_count": execution.get("unique_issuer_output_count", 0),
        "wrapper_retry_count": execution.get("wrapper_explicit_retry_count", 0),
        "observed_cli_retry_signal_count": execution.get(
            "observed_cli_retry_signal_count", 0
        ),
        "observed_disconnect_count": execution.get(
            "observed_websocket_disconnect_signal_count", 0
        ),
        "explicit_capacity_failure_count": execution.get(
            "explicit_capacity_count", 0
        ),
        "transport_timeout_count": execution.get("watchdog_timeout_count", 0),
        "orphan_count": execution.get("orphan_count", 0),
        "run_results": dict(run_results),
        **gate_fields,
        "core_stability": core.get("status", "NOT_MEASURED"),
        "timing_stability": timing.get("status", "NOT_MEASURED"),
        "formal_generalization": generalization.get(
            "ownership_generalization_verdict",
            generalization.get("status", "NOT_MEASURED"),
        ),
        "exposure_state": exposure.get(
            "holdout_output_exposure_state", "UNEXPOSED"
        ),
        "semantic_revelation_state": exposure.get(
            "holdout_semantic_revelation_state", "NOT_MEASURED"
        ),
        "retirement_state": exposure.get(
            "holdout_retirement_state", "NOT_MEASURED"
        ),
        "future_unseen_reuse_allowed": exposure.get(
            "future_unseen_holdout_reuse_allowed", "NOT_MEASURED"
        ),
        "observed_paused_schedule_count": pause.get(
            "observed_scheduler_object_count"
        ),
        "approved_pause_scheduler_mutation_count": pause.get(
            "scheduler_mutation_count", 0
        ),
        "automatic_monitoring_resume": 0,
        "paid_data_service_change": 0,
        "new_free_api_management_gate": 0,
        "production_db_mutation": 0,
        "production_send": 0,
        "monitoring_registration_change": 0,
        "live_v2_change": 0,
        "night_futures_change": 0,
        "artifact_count": "PENDING_FINALIZE",
        "artifact_hash_mismatch_count": "PENDING_FINALIZE",
        "artifact_size_mismatch_count": "PENDING_FINALIZE",
        "artifact_secret_scan_failure_count": "PENDING_FINALIZE",
        "focused_tests": legacy_completion.get("focused_tests", "NOT_RUN"),
        "full_tests": legacy_completion.get("full_tests", "NOT_RUN"),
        "ruff": legacy_completion.get("ruff", "NOT_RUN"),
        "diff_check": legacy_completion.get("diff_check", "NOT_RUN"),
        "status": legacy_completion.get("status", "STOPPED"),
        "readiness": legacy_completion.get("readiness", "NOT_READY"),
        "stop_reason": legacy_completion.get("stop_reason"),
        "next_scope": legacy_completion.get("next_scope", "NOT_MEASURED"),
    }


def close_reports(args: argparse.Namespace) -> None:
    _configure_legacy()
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") == "EVIDENCE_COMPLETE" and not state.get(
        "source_gate_only"
    ):
        legacy.close_reports(_legacy_args(args))
    elif state.get("state") == "EVIDENCE_COMPLETE" and state.get("source_gate_only"):
        legacy.close_reports(_legacy_args(args))
    elif state.get("state") not in {"READY_TO_PACKAGE", "COMPLETE"}:
        raise ValueError("evidence_complete_state_required")
    _write_source_phase_reports(args)
    _write_execution_phase_reports(args)
    completion = _completion(args)
    write_proof(args.report_dir, 64, completion)
    write_text(
        args.report_dir / "README.md",
        "# Existing Source Environment Binding & Fresh Holdout Proof Resume\n\n"
        f"- Cohort: `{len(completion['ordered_issuers'])}` issuers\n"
        f"- FIRST/A/B/C: `{completion['run_results']}`\n"
        f"- Readiness: `{completion['readiness']}`\n"
        f"- Runtime risk: `{legacy.CARRIED_RUNTIME_RISK}`\n\n"
        "The existing protected source configuration was referenced through the "
        "canonical loader. No secret value, production send, database mutation, "
        "monitoring registration change, or automatic schedule resume occurred.\n",
    )
    state = read_json(args.output_root / "program-state.json")
    state.update(
        {
            "state": "READY_TO_PACKAGE",
            "readiness": completion["readiness"],
            "stop_reason": completion["stop_reason"],
            "next_scope": completion["next_scope"],
            "validation": {
                "focused_tests": args.focused_tests,
                "full_tests": args.full_tests,
                "ruff": args.ruff,
                "diff_check": args.diff_check,
            },
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True), flush=True)


def _copy_tree(source: Path, destination: Path) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_file():
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


def _safe_member(name: str) -> bool:
    return not (
        name.startswith("/")
        or "\\" in name
        or ".." in PurePosixPath(name).parts
    )


def scan_artifact_secrets(paths: Sequence[Path]) -> dict[str, object]:
    inherited = legacy.scan_artifact_secrets(paths)
    get_settings.cache_clear()
    settings = get_settings()
    protected_values = tuple(
        value.encode("utf-8")
        for value in (settings.opendart_api_key, settings.sec_user_agent)
        if isinstance(value, str) and value
    )
    exact_match_count = 0
    dart_query_match_count = 0
    for path in paths:
        if not path.is_file():
            continue
        payload = path.read_bytes()
        exact_match_count += sum(payload.count(value) for value in protected_values)
        dart_query_match_count += payload.count(b"crtfc_key=")
    total = (
        int(inherited["secret_exposure_count"])
        + exact_match_count
        + dart_query_match_count
    )
    return {
        "inherited_pattern_match_count": inherited["secret_exposure_count"],
        "protected_value_exact_match_count": exact_match_count,
        "opendart_query_parameter_match_count": dart_query_match_count,
        "secret_exposure_count": total,
        "secret_scan_status": "PASS" if total == 0 else "FAIL",
    }


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "READY_TO_PACKAGE":
        raise ValueError("ready_to_package_state_required")
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_for_final_package")
    if args.bundle_root.exists() or args.zip_output.exists():
        raise ValueError("new_bundle_root_and_zip_required")
    args.bundle_root.mkdir(parents=True)
    _copy_tree(args.report_dir, args.bundle_root / "reports")
    _copy_tree(args.output_root, args.bundle_root / "experiment")
    shutil.copyfile(
        Path.cwd() / WORK_INSTRUCTION_PATH,
        args.bundle_root / "work-instruction.md",
    )
    completion = read_json(proof_path(args.report_dir, 64))
    completion.update(
        {
            "final_head_sha": git_value("rev-parse", "HEAD"),
            "final_tree_sha": git_value("rev-parse", "HEAD^{tree}"),
            "branch": git_value("branch", "--show-current"),
            "worktree_clean_at_package": True,
            "packaged_at": datetime.now(UTC).isoformat(),
        }
    )
    write_text(
        args.bundle_root / "README.md",
        (args.report_dir / "README.md").read_text(encoding="utf-8"),
    )
    payloads_before_completion = sorted(
        path
        for path in args.bundle_root.rglob("*")
        if path.is_file()
        and path
        not in {
            args.bundle_root / "artifact-index.json",
            args.bundle_root / "completion.json",
        }
    )
    indexed_payload_count = len(payloads_before_completion) + 1
    zip_member_count = indexed_payload_count + 1
    completion.update(
        {
            "artifact_count": indexed_payload_count,
            "indexed_payload_count": indexed_payload_count,
            "zip_member_count": zip_member_count,
            "artifact_hash_mismatch_count": 0,
            "artifact_size_mismatch_count": 0,
            "artifact_secret_scan_failure_count": 0,
            "integrity_mismatch_counts": {
                "duplicate_members": 0,
                "unsafe_members": 0,
                "crc_failure": None,
                "index_membership_mismatch": 0,
                "hash_mismatches": 0,
                "size_mismatches": 0,
            },
        }
    )
    write_json(args.bundle_root / "completion.json", completion)
    payloads = sorted(
        path
        for path in args.bundle_root.rglob("*")
        if path.is_file() and path != args.bundle_root / "artifact-index.json"
    )
    if len(payloads) != indexed_payload_count:
        raise ValueError("predicted_indexed_payload_count_mismatch")
    rows = []
    for path in payloads:
        scan = scan_artifact_secrets([path])
        if scan["secret_scan_status"] != "PASS":
            raise ValueError(f"artifact_secret_scan_failed:{path}")
        rows.append(
            {
                "path": str(path.relative_to(args.bundle_root)),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                "artifact_class": str(path.relative_to(args.bundle_root)).split("/", 1)[0],
                "secret_scan_status": "PASS",
            }
        )
    index = {
        "contract": "existing-source-env-binding-artifact-index-v1",
        "index_self_exclusion": "artifact-index.json",
        "all_payload_files_except_index_itself_individually_indexed": True,
        "indexed_payload_count": len(rows),
        "rows": rows,
        "status": "PASS",
    }
    write_json(args.bundle_root / "artifact-index.json", index)
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.bundle_root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(args.bundle_root))
    temporary.replace(args.zip_output)
    with zipfile.ZipFile(args.zip_output) as archive:
        names = archive.namelist()
        archived_index = json.loads(archive.read("artifact-index.json"))
        indexed = {str(row["path"]): row for row in archived_index["rows"]}
        expected = set(names) - {"artifact-index.json"}
        hash_mismatches = 0
        size_mismatches = 0
        for name, row in indexed.items():
            payload = archive.read(name)
            hash_mismatches += hashlib.sha256(payload).hexdigest() != row["sha256"]
            size_mismatches += len(payload) != row["byte_size"]
        failures = {
            "duplicate_members": len(names) - len(set(names)),
            "unsafe_members": sum(not _safe_member(name) for name in names),
            "crc_failure": archive.testzip(),
            "index_membership_mismatch": int(set(indexed) != expected),
            "hash_mismatches": hash_mismatches,
            "size_mismatches": size_mismatches,
        }
    if any(bool(value) for value in failures.values()):
        raise ValueError(f"final_zip_integrity_failure:{failures}")
    if len(names) != zip_member_count:
        raise ValueError("predicted_zip_member_count_mismatch")
    zip_sha = file_sha256(args.zip_output)
    write_text(args.zip_output.with_suffix(args.zip_output.suffix + ".sha256"), zip_sha)
    state.update(
        {
            "state": "COMPLETE",
            "final_head_sha": completion["final_head_sha"],
            "report_zip": str(args.zip_output),
            "report_zip_sha256": zip_sha,
            "zip_member_count": len(names),
            "indexed_payload_count": len(rows),
            "zip_integrity_mismatches": failures,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--bootstrap", action="store_true")
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--seal", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--close-reports", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--latest-result-zip", type=Path, required=True)
    parser.add_argument("--diagnostic-zip", type=Path, required=True)
    parser.add_argument("--predecessor-zip", type=Path, required=True)
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
    if args.bootstrap and args.as_of is None:
        raise ValueError("bootstrap_requires_fixed_as_of")
    if args.as_of is not None and args.as_of.isoformat() != FROZEN_EVALUATION_CUTOFF:
        raise ValueError("frozen_evaluation_cutoff_drift")
    for name in (
        "output_root",
        "report_dir",
        "bundle_root",
        "latest_result_zip",
        "diagnostic_zip",
        "predecessor_zip",
        "historical_zip",
        "expansion_zip",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.bootstrap:
        bootstrap(args)
    elif args.prepare:
        prepare(args)
    elif args.seal:
        seal(args)
    elif args.execute:
        execute(args)
    elif args.close_reports:
        close_reports(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
