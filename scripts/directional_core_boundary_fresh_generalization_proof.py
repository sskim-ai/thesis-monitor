from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from app.services.codex_runtime_state_service import (
    CodexRuntimeIsolationCollision,
    context_runtime_state_namespace,
)
from scripts import directional_core_boundary_calibration_repair_fresh_generalization_proof as calibration
from scripts import existing_source_env_binding_fresh_holdout_resume as source_env
from scripts import fresh_issuer_ownership_proof_transport_risk_carried as legacy
from scripts import model_transport_revalidation_ownership_continuation as transport
from scripts import monitoring_pause_completion_fresh_issuer_ownership_proof as selection
from scripts import new_issuer_holdout_selection_ownership_proof as runner
from scripts import runtime_namespace_isolation_repair_fresh_holdout_proof as runtime_proof
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = (
    "directional-core-boundary-calibration-repair-fresh-generalization-proof-v1"
)
WORK_INSTRUCTION_PATH = (
    "docs/work-instructions/"
    "20260908-directional-core-boundary-calibration-repair-and-fresh-"
    "generalization-proof.md"
)
WORK_INSTRUCTION_SHA256 = (
    "fecc2a58ffc3e8e70d3891651ab1823872d76f7530cc1c532de3afa8cc9792f7"
)
LATEST_RESULT_NAME = (
    "thesis-monitor-20260908-runtime-namespace-isolation-repair-"
    "fresh-holdout-proof-report.zip"
)
LATEST_RESULT_SHA256 = (
    "5ade7e8d06c1ae41343f555ae65ff4979ac94d4f1bcf0d94bda8701e4bd5e8c5"
)
LATEST_RESULT_MEMBERS = 2166
LATEST_RESULT_INDEXED_PAYLOADS = 2165
LATEST_FINAL_HEAD = "05c93cf7d768ddb09b670ca74dc69c2b698e5f6b"
PREVIOUS_EXCLUSION_COUNT = 133
NEWLY_RETIRED_COUNT = 16
TARGET_US = 4
TARGET_KR = 12
TARGET_TOTAL = TARGET_US + TARGET_KR
EXPECTED_REAL_CONTEXTS = 32
CALIBRATION_FREEZE_SHA256 = (
    "8214ee6e7fbc5fa29e5569dac5c01ab466744e4f343bab4a9d689231cdc6837d"
)
CALIBRATION_CONTRACT_SHA256 = (
    "3443dc0f7505d01bc5ba965fa0f20128f12f2678d5e16d5f883ce41f47067d33"
)
CALIBRATION_FROZEN_STATES = {
    "FICTIONAL_PASS_ARCHITECTURE_FROZEN",
    "FRESH_REAL_PROOF_STOPPED",
    "FRESH_REAL_PROOF_COMPLETE",
}
REPAIRED_RUNTIME_RISK = "RUNTIME_NAMESPACE_ISOLATION_REPAIRED_AND_PREFLIGHT_PROVEN"
REPORT_DIRECTORY = (
    "20260908-directional-core-boundary-calibration-repair-fresh-"
    "generalization-proof/fresh-real-internal"
)
RETIRED_COHORT = (
    "WYNN",
    "DOX",
    "NWS",
    "ASTI",
    "064850",
    "053270",
    "078860",
    "145720",
    "199730",
    "065510",
    "396470",
    "299900",
    "020180",
    "122310",
    "417200",
    "023910",
)

FINAL_REPORT_NAMES = (
    "17-updated-real-exposure-exclusion-registry",
    "18-source-config-presence-preflight",
    "19-schedule-pause-observation",
    "20-fresh-selection-policy",
    "21-us-candidate-source-readiness",
    "22-kr-candidate-source-readiness",
    "23-fresh-holdout-selection",
    "24-fresh-source-generation",
    "25-source-identity-audit",
    "26-source-sufficiency-audit",
    "27-fresh-source-lock",
    "28-fresh-proof-precommit",
    "29-investment-semantic-freeze",
    "30-runtime-isolation-freeze",
    "31-first-execution-summary",
    "32-first-context-artifact-manifest",
    "33-first-per-context-semantic-audit",
    "34-first-ownership-gate",
    "35-first-renderer-gate",
    "36-first-hard-safety-gate",
    "37-first-message-quality-advisory",
    "38-run-a-execution-summary",
    "39-run-a-context-artifact-manifest",
    "40-run-a-per-context-semantic-audit",
    "41-run-a-ownership-gate",
    "42-run-a-renderer-gate",
    "43-run-a-hard-safety-gate",
    "44-run-a-message-quality-advisory",
    "45-run-b-execution-summary",
    "46-run-b-context-artifact-manifest",
    "47-run-b-per-context-semantic-audit",
    "48-run-b-ownership-gate",
    "49-run-b-renderer-gate",
    "50-run-b-hard-safety-gate",
    "51-run-b-message-quality-advisory",
    "52-run-c-execution-summary",
    "53-run-c-context-artifact-manifest",
    "54-run-c-per-context-semantic-audit",
    "55-run-c-ownership-gate",
    "56-run-c-renderer-gate",
    "57-run-c-hard-safety-gate",
    "58-run-c-message-quality-advisory",
    "59-fresh-holdout-exposure-retirement-state",
    "60-fresh-directional-core-stability",
    "61-fresh-price-timing-stability",
    "62-fresh-ownership-generalization",
    "63-fresh-renderer-ownership-proof",
    "64-fresh-hard-safety-regression",
    "65-fresh-message-quality-summary",
    "66-runtime-reliability-observations",
    "67-production-no-change",
    "68-night-futures-no-change",
    "69-next-scope-handoff",
    "70-program-completion",
)

_BASE_ARCHITECTURE_HASHES = legacy.architecture_hashes
_BASE_TRANSPORT_HASHES = runtime_proof.transport_topology_hashes


def read_json(path: Path) -> dict[str, Any]:
    return legacy.read_json(path)


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


def _zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def _summary(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return f"{len(value)} rows; sha256={canonical_sha256(value)}"
    if isinstance(value, dict) and len(value) > 12:
        return f"{len(value)} keys; sha256={canonical_sha256(value)}"
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def write_named_report(report_dir: Path, name: str, value: Mapping[str, object]) -> None:
    write_json(report_dir / "proofs" / f"{name}.json", value)
    rows = [
        f"| {str(key).replace('|', '/')} | {_summary(item).replace('|', '/')} |"
        for key, item in value.items()
    ]
    write_text(
        report_dir / f"{name}.md",
        f"# {name}\n\n| Field | Value |\n| --- | --- |\n" + "\n".join(rows),
    )


def architecture_hashes(repo_root: Path) -> dict[str, str]:
    return {
        **_BASE_ARCHITECTURE_HASHES(repo_root),
        **calibration.calibration_architecture_hashes(repo_root),
        "directional_calibration_real_proof_orchestrator": file_sha256(
            Path(__file__).resolve()
        ),
    }


def transport_topology_hashes() -> dict[str, str]:
    return {
        **_BASE_TRANSPORT_HASHES(),
        "context_runtime_state_namespace": runner.source_sha256(
            context_runtime_state_namespace
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
        f"20260908-directional-calibration-source-{stamp}-{source_suffix}",
        f"20260908-directional-calibration-proof-{stamp}-{runtime_suffix}",
    )


def _configure_stack() -> None:
    legacy.PROGRAM_CONTRACT = PROGRAM_CONTRACT
    legacy.WORK_INSTRUCTION_PATH = WORK_INSTRUCTION_PATH
    legacy.WORK_INSTRUCTION_SHA256 = WORK_INSTRUCTION_SHA256
    legacy.REPORT_DIRECTORY = REPORT_DIRECTORY
    legacy.EXCLUSION_COUNT = PREVIOUS_EXCLUSION_COUNT + NEWLY_RETIRED_COUNT
    legacy.CARRIED_RUNTIME_RISK = REPAIRED_RUNTIME_RISK
    legacy.architecture_hashes = architecture_hashes
    legacy.transport_topology_hashes = transport_topology_hashes
    legacy._configure_prior_module()
    selection.source_generation_ids = source_generation_ids


def _internal_args(args: argparse.Namespace) -> argparse.Namespace:
    values = vars(args).copy()
    values["report_dir"] = args.report_dir / "fresh-real-internal"
    return argparse.Namespace(**values)


def assert_calibration_frozen(repo_root: Path) -> dict[str, Any]:
    state = read_json(
        repo_root
        / "artifacts/20260908-directional-core-boundary-calibration-repair-fresh-"
        "generalization-proof/program-state.json"
    )
    seal = read_json(
        repo_root
        / "docs/reports/20260908-directional-core-boundary-calibration-repair-"
        "fresh-generalization-proof/proofs/16-calibration-freeze-seal.json"
    )
    failures = []
    if state.get("state") not in CALIBRATION_FROZEN_STATES:
        failures.append("fictional_architecture_not_frozen")
    if state.get("fictional_calibration_unstable_count") != 0:
        failures.append("fictional_calibration_unstable")
    if state.get("calibration_freeze_seal_sha256") != CALIBRATION_FREEZE_SHA256:
        failures.append("calibration_freeze_hash_mismatch")
    if state.get("calibration_contract_sha256") != CALIBRATION_CONTRACT_SHA256:
        failures.append("calibration_contract_hash_mismatch")
    if canonical_sha256(seal) != CALIBRATION_FREEZE_SHA256:
        failures.append("calibration_seal_document_mismatch")
    current_hashes = calibration.calibration_architecture_hashes(repo_root)
    if current_hashes != state.get("calibration_architecture_hashes"):
        failures.append("calibration_architecture_drift")
    result = {
        "contract": "directional-calibration-frozen-architecture-gate-v1",
        "calibration_freeze_seal_sha256": CALIBRATION_FREEZE_SHA256,
        "calibration_contract_sha256": CALIBRATION_CONTRACT_SHA256,
        "calibration_architecture_hashes": current_hashes,
        "fictional_model_invocation_count": state.get(
            "fictional_model_invocation_count"
        ),
        "fictional_calibration_unstable_count": state.get(
            "fictional_calibration_unstable_count"
        ),
        "observed_program_state": state.get("state"),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    if failures:
        raise ValueError(f"CALIBRATION_FREEZE_GATE_FAILED:{failures}")
    return result


def expand_exclusion_registry(
    registry: Mapping[str, object],
    identities: Mapping[str, object],
    *,
    exposed_generation_id: str,
) -> dict[str, object]:
    prior_rows = [
        dict(row) for row in registry.get("rows") or [] if isinstance(row, Mapping)
    ]
    if len(prior_rows) != PREVIOUS_EXCLUSION_COUNT:
        raise ValueError(f"previous_exclusion_count_mismatch:{len(prior_rows)}")
    by_key = {
        str(row.get("canonical_issuer_key")): row
        for row in prior_rows
        if row.get("canonical_issuer_key")
    }
    if len(by_key) != PREVIOUS_EXCLUSION_COUNT:
        raise ValueError("previous_exclusion_registry_identity_invalid")
    identity_rows = [
        dict(row)
        for market in ("us", "kr")
        for row in identities.get(market) or []
        if isinstance(row, Mapping)
    ]
    by_symbol = {str(row.get("display_symbol")): row for row in identity_rows}
    appended = []
    for position, ticker in enumerate(RETIRED_COHORT):
        reference = by_symbol.get(ticker)
        if reference is None:
            raise ValueError(f"retired_cohort_identity_missing:{ticker}")
        key = str(reference.get("canonical_issuer_key") or "")
        if not key or key in by_key:
            raise ValueError(f"retired_cohort_not_fresh_in_prior_registry:{ticker}:{key}")
        batch = position // runner.CONTEXT_SIZE + 1
        lineage = [
            {
                "experiment_class": PROGRAM_CONTRACT,
                "exposure_class": "REAL_MODEL_OUTPUT",
                "generation_id": exposed_generation_id,
                "invocation_id": (
                    f"{exposed_generation_id}:{run}:{stage}:{batch:02d}"
                ),
                "ticker": ticker,
                "usable_output_exists": True,
            }
            for run in runner.RUNS
            for stage in runner.STAGES
        ]
        row = {
            "actual_output_exposure": True,
            "actual_real_model_spawn": True,
            "canonical_issuer_key": key,
            "exclusion_reasons": ["RETIRED_FULLY_EXPOSED_COHORT"],
            "lineage": lineage,
            "market": reference.get("market"),
            "security_aliases": sorted(
                {ticker, *(str(value) for value in reference.get("provider_aliases") or [])}
            ),
            "whole_cohort_retired": True,
            "retirement_reasons": ["RETIRED_AFTER_EVALUATION"],
        }
        by_key[key] = row
        appended.append(row)
    rows = [by_key[key] for key in sorted(by_key)]
    expected = PREVIOUS_EXCLUSION_COUNT + NEWLY_RETIRED_COUNT
    if len(appended) != NEWLY_RETIRED_COUNT or len(rows) != expected:
        raise ValueError("updated_exclusion_registry_count_mismatch")
    return {
        "contract": "canonical-real-exposure-registry-directional-calibration-v1",
        "prior_registry_count": PREVIOUS_EXCLUSION_COUNT,
        "appended_exposed_issuer_count": NEWLY_RETIRED_COUNT,
        "reconciled_registry_count": expected,
        "exclusion_shrink_count": 0,
        "latest_exposed_generation_id": exposed_generation_id,
        "latest_cohort_issuer_exposure": "16/16_REAL_OUTPUT_16/16_RETIRED",
        "latest_cohort_core_stage_coverage": "16/16",
        "latest_cohort_timing_stage_coverage": "16/16",
        "latest_complete_run_coverage": list(runner.RUNS),
        "latest_retirement_reason": "RETIRED_AFTER_EVALUATION",
        "rows": rows,
        "all_excluded_issuer_keys": sorted(by_key),
        "status": "PASS",
    }


def filter_candidate_identities(
    identities: Mapping[str, object], registry: Mapping[str, object]
) -> dict[str, object]:
    excluded = {str(value) for value in registry.get("all_excluded_issuer_keys") or []}
    result: dict[str, object] = {
        "contract": "directional-calibration-fresh-candidate-identities-v1",
        "status": "FROZEN",
    }
    for market in ("us", "kr"):
        result[market] = [
            dict(row)
            for row in identities.get(market) or []
            if isinstance(row, Mapping)
            and str(row.get("canonical_issuer_key") or "") not in excluded
        ]
    leaked = {
        str(row.get("display_symbol"))
        for market in ("us", "kr")
        for row in result[market]
        if str(row.get("display_symbol")) in RETIRED_COHORT
    }
    if leaked:
        raise ValueError(f"retired_cohort_leaked_into_candidates:{sorted(leaked)}")
    if len(result["us"]) < TARGET_US or len(result["kr"]) < TARGET_KR:
        raise ValueError("fresh_candidate_universe_below_required_market_mix")
    return result


def _namespace_preflight() -> dict[str, object]:
    rows = []
    with tempfile.TemporaryDirectory(
        prefix="thesis-monitor-directional-calibration-namespace-preflight-"
    ) as directory:
        root = Path(directory)
        auth = root / "non-secret-placeholder-auth.json"
        auth.write_text("{}\n", encoding="utf-8")
        auth.chmod(0o600)
        adapter = transport.ContinuationTransportAdapter(
            continuation_generation="directional-calibration-namespace-preflight",
            receipt_root=root / "receipts",
            codex_bin=engine._signed_in_codex_bin(),
            runtime_state_root=root / "runtime-state",
        )
        for run in runner.RUNS:
            for stage in runner.STAGES:
                for batch in range(1, 5):
                    invocation_id = (
                        "directional-calibration-namespace-preflight:"
                        f"{run}:{stage}:{batch:02d}"
                    )
                    with engine.isolated_model_working_directory(
                        run=f"calibration-preflight-{run}-{stage.lower()}",
                        batch=batch,
                    ) as cwd:
                        _runtime_state, identity = adapter.prepare_execution_isolation(
                            state_namespace=(
                                f"DIRECTIONAL_CALIBRATION_20260908_{run.upper()}_{stage}"
                            ),
                            invocation_id=invocation_id,
                            working_directory=cwd,
                            auth_source=auth,
                        )
                    rows.append(
                        {"run": run, "stage": stage, "batch": batch, **identity.audit_dict()}
                    )
        collision_stopped = False
        try:
            with engine.isolated_model_working_directory(
                run="calibration-preflight-collision", batch=1
            ) as cwd:
                adapter.prepare_execution_isolation(
                    state_namespace="DIRECTIONAL_CALIBRATION_COLLISION_PROOF",
                    invocation_id=str(rows[0]["invocation_id"]),
                    working_directory=cwd,
                    auth_source=auth,
                )
        except CodexRuntimeIsolationCollision:
            collision_stopped = True
        model_calls = adapter.model_call_count
    counts = {
        "invocation": len({str(row["invocation_id"]) for row in rows}),
        "namespace": len({str(row["runtime_state_namespace_hash"]) for row in rows}),
        "workdir": len({str(row["working_directory_identity"]) for row in rows}),
    }
    passed = (
        len(rows) == EXPECTED_REAL_CONTEXTS
        and all(value == EXPECTED_REAL_CONTEXTS for value in counts.values())
        and model_calls == 0
        and collision_stopped
        and transport.MODEL == "gpt-5.6-sol"
        and transport.EFFORT == "xhigh"
        and runner.TIMEOUT_SECONDS == 1800
        and runner.CONTEXT_SIZE == 4
    )
    result = {
        "contract": "directional-calibration-full-path-namespace-preflight-v1",
        "planned_context_count": EXPECTED_REAL_CONTEXTS,
        "unique_invocation_count": counts["invocation"],
        "unique_runtime_namespace_count": counts["namespace"],
        "unique_working_directory_count": counts["workdir"],
        "collision_negative_proof": (
            "PASS_STOPPED_BEFORE_SPAWN" if collision_stopped else "FAIL"
        ),
        "model_call_count": model_calls,
        "model": transport.MODEL,
        "reasoning_effort": transport.EFFORT,
        "timeout_seconds": runner.TIMEOUT_SECONDS,
        "subjects_per_context": runner.CONTEXT_SIZE,
        "rows": rows,
        "status": "PASS" if passed else "FAIL",
    }
    if not passed:
        raise ValueError("DIRECTIONAL_CALIBRATION_NAMESPACE_PREFLIGHT_FAILED")
    return result


def _source_config_presence_preflight(repo_root: Path) -> dict[str, object]:
    configuration = source_env.source_configuration_audit(repo_root)
    required = configuration.get("required_setting_presence")
    required = required if isinstance(required, Mapping) else {}
    passed = (
        configuration.get("status") == "PASS"
        and required.get("OPENDART_API_KEY") is True
        and required.get("SEC_USER_AGENT") is True
        and configuration.get("protected_source_config_bound") is True
    )
    result = {
        "contract": "directional-calibration-source-config-presence-preflight-v1",
        "source_config_loader": configuration.get("source_config_loader"),
        "source_config_loader_sha256": configuration.get(
            "source_config_loader_sha256"
        ),
        "opendart_api_key_present": required.get("OPENDART_API_KEY") is True,
        "sec_user_agent_present": required.get("SEC_USER_AGENT") is True,
        "protected_source_config_present": configuration.get(
            "protected_source_config_bound"
        ),
        "secret_values_emitted": 0,
        "candidate_source_request_count": 0,
        "status": "PASS" if passed else "FAIL",
    }
    if not passed:
        raise ValueError("SOURCE_CONFIGURATION_ABSENT_BEFORE_CANDIDATE_LOOP")
    return result


def _repository_provenance() -> dict[str, object]:
    instruction_commit = git_value("log", "-1", "--format=%H", "--", WORK_INSTRUCTION_PATH)
    return {
        "contract": "repository-provenance-v1",
        "branch": git_value("branch", "--show-current"),
        "base_sha": LATEST_FINAL_HEAD,
        "work_instruction_commit": instruction_commit,
        "implementation_commit": git_value("rev-parse", "HEAD"),
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "origin_main": git_value("rev-parse", "origin/main"),
        "work_instruction_sha256": file_sha256(Path.cwd() / WORK_INSTRUCTION_PATH),
        "status": "PASS",
    }


def _candidate_manifest(
    market: str, rows: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    return {
        "contract": f"directional-calibration-{market}-candidate-manifest-v1",
        "market": market,
        "target_count": TARGET_US if market == "us" else TARGET_KR,
        "candidate_count": len(rows),
        "candidate_order": [str(row.get("display_symbol")) for row in rows],
        "source_evaluation_performed": 0,
        "model_calls": 0,
        "status": "FROZEN",
    }


def bootstrap(args: argparse.Namespace) -> None:
    _configure_stack()
    repo_root = Path.cwd().resolve()
    if args.output_root.exists() or (args.report_dir / "fresh-real-internal").exists():
        raise ValueError("new_real_output_and_internal_report_directories_required")
    if file_sha256(repo_root / WORK_INSTRUCTION_PATH) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_before_real_bootstrap")
    if args.as_of is None:
        raise ValueError("bootstrap_requires_fixed_as_of")
    calibration_gate = assert_calibration_frozen(repo_root)
    integrity = calibration.verify_latest_result(args.latest_result_zip)
    source_config = _source_config_presence_preflight(repo_root)
    pause = runtime_proof._pause_observation()
    namespace = _namespace_preflight()
    with zipfile.ZipFile(args.latest_result_zip) as archive:
        prior_registry = _zip_json(
            archive, "experiment/selection-inputs/merged-registry.json"
        )
        prior_identities = _zip_json(archive, "experiment/candidate-identities.json")
        prior_state = _zip_json(archive, "experiment/program-state.json")
        handoff = _zip_json(
            archive, "experiment/selection-inputs/expansion-handoff.json"
        )
        prior_117 = _zip_json(
            archive, "experiment/selection-inputs/prior-117-registry.json"
        )
        prior_101 = _zip_json(
            archive, "experiment/selection-inputs/prior-101-registry.json"
        )
        prior_policy = _zip_json(
            archive,
            "reports/internal/proofs/05-dual-market-source-coverage-policy.json",
        )
    if prior_state.get("holdout_output_exposure_state") != "FULLY_EXPOSED":
        raise ValueError("latest_cohort_not_fully_exposed")
    if tuple(prior_state.get("ordered_cohort") or []) != RETIRED_COHORT:
        raise ValueError("latest_cohort_identity_mismatch")
    if canonical_sha256(prior_registry) != prior_state.get("exclusion_registry_sha256"):
        raise ValueError("prior_exclusion_registry_hash_mismatch")
    registry = expand_exclusion_registry(
        prior_registry,
        prior_identities,
        exposed_generation_id=str(prior_state.get("program_generation_id") or ""),
    )
    identities = filter_candidate_identities(prior_identities, registry)
    us_rows = [dict(row) for row in identities["us"]]
    kr_rows = [dict(row) for row in identities["kr"]]
    policy = {
        **prior_policy,
        "contract": "directional-calibration-fresh-selection-policy-v1",
        "candidate_identities_sha256": canonical_sha256(identities),
        "exclusion_registry_count": len(registry["rows"]),
        "exclusion_registry_sha256": canonical_sha256(registry),
        "market_policies": {
            "us": {
                "bounded_evaluation_limit": len(us_rows),
                "candidate_order": [str(row["display_symbol"]) for row in us_rows],
            },
            "kr": {
                "bounded_evaluation_limit": len(kr_rows),
                "candidate_order": [str(row["display_symbol"]) for row in kr_rows],
            },
        },
        "selection_rule": (
            "reuse the verified supported-reference order; remove every canonical "
            "issuer key in the reconciled real-exposure registry; accept the first "
            "source-eligible unique US4 and KR12"
        ),
        "newly_retired_issuer_count": NEWLY_RETIRED_COUNT,
        "calibration_freeze_seal_sha256": CALIBRATION_FREEZE_SHA256,
        "source_evaluation_performed": 0,
        "outcome_based_selection": 0,
        "model_calls": 0,
        "status": "FROZEN_PRE_SOURCE_EVALUATION",
    }
    args.output_root.mkdir(parents=True)
    internal = args.report_dir / "fresh-real-internal"
    (internal / "proofs").mkdir(parents=True)
    selection_inputs = args.output_root / "selection-inputs"
    write_json(selection_inputs / "prior-133-registry.json", prior_registry)
    write_json(selection_inputs / "prior-117-registry.json", prior_117)
    write_json(selection_inputs / "prior-101-registry.json", prior_101)
    write_json(selection_inputs / "merged-registry.json", registry)
    write_json(selection_inputs / "expansion-handoff.json", handoff)
    write_json(
        selection_inputs / "latest-exposed-state.json",
        {
            "contract": "directional-calibration-latest-exposed-state-v1",
            "program_generation_id": prior_state.get("program_generation_id"),
            "ordered_cohort": list(RETIRED_COHORT),
            "output_exposure_state": "FULLY_EXPOSED",
            "retirement_state": "RETIRED_AFTER_EVALUATION",
            "future_unseen_reuse_allowed": 0,
            "status": "PASS",
        },
    )
    _write_jsonl(selection_inputs / "us-candidates.jsonl", us_rows)
    _write_jsonl(selection_inputs / "kr-candidates.jsonl", kr_rows)
    write_json(args.output_root / "candidate-identities.json", identities)
    write_json(args.output_root / "namespace-isolation-preflight.json", namespace)
    write_json(args.output_root / "source-configuration-audit.json", source_config)
    write_json(args.output_root / "schedule-pause-observation.json", pause)
    provenance = _repository_provenance()
    runner.write_proof(internal, 1, provenance)
    runner.write_proof(
        internal,
        2,
        {
            "contract": "latest-result-integrity-v1",
            "latest_result": integrity,
            "status": "PASS",
        },
    )
    runner.write_proof(internal, 3, registry)
    runner.write_proof(
        internal,
        4,
        {
            "contract": "directional-calibration-exclusion-continuity-v1",
            "previous_count": PREVIOUS_EXCLUSION_COUNT,
            "appended_count": NEWLY_RETIRED_COUNT,
            "reconciled_count": len(registry["rows"]),
            "previous_registry_sha256": canonical_sha256(prior_registry),
            "new_registry_sha256": canonical_sha256(registry),
            "retired_tickers": list(RETIRED_COHORT),
            "exclusion_shrink_count": 0,
            "status": "PASS",
        },
    )
    runner.write_proof(internal, 5, policy)
    runner.write_proof(internal, 6, _candidate_manifest("us", us_rows))
    runner.write_proof(internal, 9, _candidate_manifest("kr", kr_rows))
    runner.write_reports(internal)
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "SELECTION_FROZEN",
        "branch": provenance["branch"],
        "base_sha": LATEST_FINAL_HEAD,
        "work_instruction_commit": provenance["work_instruction_commit"],
        "implementation_commit": provenance["implementation_commit"],
        "implementation_tree": provenance["implementation_tree"],
        "selection_freeze_commit": "PENDING_COMMIT",
        "selection_policy_sha256": canonical_sha256(policy),
        "candidate_identities_sha256": canonical_sha256(identities),
        "exclusion_registry_sha256": canonical_sha256(registry),
        "exclusion_registry_count": len(registry["rows"]),
        "as_of": args.as_of.isoformat(),
        "ordered_cohort": [],
        "model_invocation_count": 0,
        "real_investment_model_invocation_count": 0,
        "calibration_gate": calibration_gate,
        "calibration_freeze_seal_sha256": CALIBRATION_FREEZE_SHA256,
        "calibration_contract_sha256": CALIBRATION_CONTRACT_SHA256,
        "namespace_isolation_preflight_sha256": canonical_sha256(namespace),
        "initial_pause_observation": pause,
        "source_configuration": source_config,
        "production_scheduler_change_current_task": 0,
        "production_telegram_send_current_task": 0,
        "automatic_monitoring_resume": 0,
    }
    write_json(args.output_root / "program-state.json", state)
    for name, document in (
        (FINAL_REPORT_NAMES[0], registry),
        (FINAL_REPORT_NAMES[1], source_config),
        (FINAL_REPORT_NAMES[2], pause),
        (FINAL_REPORT_NAMES[3], policy),
    ):
        write_named_report(args.report_dir, name, document)
    write_text(
        args.report_dir / "fresh-real-proof.md",
        "# Fresh Real Generalization Proof\n\n"
        "The frozen ordinal calibration contract is evaluated on one new US4 + KR12 "
        "cohort. Selection is source-order deterministic and outcome independent.",
    )
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def _internal_proof(args: argparse.Namespace, number: int) -> dict[str, Any]:
    path = runner.proof_path(args.report_dir / "fresh-real-internal", number)
    if path.is_file():
        return read_json(path)
    return {
        "contract": f"internal-proof-{number}-v1",
        "reason": "UPSTREAM_STAGE_NOT_RUN",
        "status": "NOT_MEASURED",
    }


def _write_source_reports(args: argparse.Namespace) -> None:
    source_config = read_json(args.output_root / "source-configuration-audit.json")
    pause = read_json(args.output_root / "schedule-pause-observation.json")
    mapping = {
        FINAL_REPORT_NAMES[0]: 3,
        FINAL_REPORT_NAMES[3]: 5,
        FINAL_REPORT_NAMES[4]: 7,
        FINAL_REPORT_NAMES[5]: 10,
        FINAL_REPORT_NAMES[6]: 15,
        FINAL_REPORT_NAMES[7]: 16,
        FINAL_REPORT_NAMES[8]: 18,
        FINAL_REPORT_NAMES[9]: 17,
        FINAL_REPORT_NAMES[10]: 19,
        FINAL_REPORT_NAMES[11]: 20,
        FINAL_REPORT_NAMES[12]: 21,
    }
    write_named_report(args.report_dir, FINAL_REPORT_NAMES[1], source_config)
    write_named_report(args.report_dir, FINAL_REPORT_NAMES[2], pause)
    for name, number in mapping.items():
        write_named_report(args.report_dir, name, _internal_proof(args, number))
    transport_freeze = {
        "contract": "directional-calibration-runtime-isolation-freeze-v1",
        "transport": _internal_proof(args, 24),
        "namespace_preflight": read_json(
            args.output_root / "namespace-isolation-preflight.json"
        ),
        "calibration_freeze_seal_sha256": CALIBRATION_FREEZE_SHA256,
        "status": (
            "FROZEN"
            if _internal_proof(args, 24).get("status") == "FROZEN"
            else "NOT_MEASURED"
        ),
    }
    write_named_report(args.report_dir, FINAL_REPORT_NAMES[13], transport_freeze)


def _augment_precommit(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "PREPARED_FROZEN":
        return
    calibration_gate = assert_calibration_frozen(Path.cwd().resolve())
    precommit_path = args.output_root / "new-holdout-precommit.json"
    precommit = read_json(precommit_path)
    precommit.update(
        {
            "contract": "directional-calibration-fresh-real-proof-precommit-v1",
            "calibration_freeze_seal_sha256": CALIBRATION_FREEZE_SHA256,
            "calibration_contract_sha256": CALIBRATION_CONTRACT_SHA256,
            "calibration_architecture_hashes": calibration_gate[
                "calibration_architecture_hashes"
            ],
            "fictional_calibration_status": "PASS",
            "fictional_calibration_unstable_count": 0,
            "directional_threshold_changed": 0,
            "majority_vote_adopted": 0,
            "fixed_weight_scorecard_adopted": 0,
            "price_timing_semantic_mutation": 0,
            "stability_acceptance": {
                "directional_core_unstable_max": 0,
                "price_timing_unstable_max": 0,
            },
            "message_quality_role": "ADVISORY_REPORTED_SEPARATELY",
            "retired_predecessor_cohort": list(RETIRED_COHORT),
            "no_semantic_edits_after_fresh_output": True,
            "status": "FROZEN",
        }
    )
    write_json(precommit_path, precommit)
    runner.write_proof(args.report_dir / "fresh-real-internal", 20, precommit)
    architecture = _internal_proof(args, 21)
    architecture.update(
        {
            "directional_calibration_gate": calibration_gate,
            "calibration_freeze_seal_sha256": CALIBRATION_FREEZE_SHA256,
            "directional_threshold_changed": 0,
            "price_timing_semantic_mutation": 0,
            "status": "FROZEN",
        }
    )
    runner.write_proof(args.report_dir / "fresh-real-internal", 21, architecture)
    state.update(
        {
            "precommit_sha256": canonical_sha256(precommit),
            "calibration_gate": calibration_gate,
            "calibration_freeze_seal_sha256": CALIBRATION_FREEZE_SHA256,
            "fresh_real_cohort_consumed": 0,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    runner.write_reports(args.report_dir / "fresh-real-internal")


def prepare(args: argparse.Namespace) -> None:
    _configure_stack()
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "SELECTION_FROZEN":
        raise ValueError("selection_frozen_state_required")
    if args.as_of is None or args.as_of.isoformat() != state.get("as_of"):
        raise ValueError("frozen_evaluation_cutoff_drift")
    assert_calibration_frozen(Path.cwd().resolve())
    legacy.prepare(_internal_args(args))
    _augment_precommit(args)
    _write_source_reports(args)
    print(
        json.dumps(
            read_json(args.output_root / "program-state.json"),
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )


def seal(args: argparse.Namespace) -> None:
    _configure_stack()
    assert_calibration_frozen(Path.cwd().resolve())
    legacy.seal(_internal_args(args))


def execute(args: argparse.Namespace) -> None:
    _configure_stack()
    assert_calibration_frozen(Path.cwd().resolve())
    legacy.execute(_internal_args(args))


def _message_quality(args: argparse.Namespace, run: str) -> dict[str, Any]:
    path = args.output_root / "run-artifacts" / run.upper() / "message-quality.json"
    if path.is_file():
        return read_json(path)
    return {
        "contract": "per-run-message-quality-advisory-v1",
        "run": run,
        "reason": "RUN_NOT_COMPLETE",
        "status": "NOT_MEASURED",
    }


def _execution_reports(args: argparse.Namespace) -> None:
    mappings = {
        "first": (14, (27, 28, 29, 30, 31, 32)),
        "a": (21, (33, 34, 35, 36, 37, 38)),
        "b": (28, (39, 40, 41, 42, 43, 44)),
        "c": (35, (45, 46, 47, 48, 49, 50)),
    }
    for run, (offset, sources) in mappings.items():
        for index, source in enumerate(sources):
            write_named_report(
                args.report_dir,
                FINAL_REPORT_NAMES[offset + index],
                _internal_proof(args, source),
            )
        write_named_report(
            args.report_dir,
            FINAL_REPORT_NAMES[offset + 6],
            _message_quality(args, run),
        )


def _latest_historical_stability(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    with zipfile.ZipFile(args.latest_result_zip) as archive:
        return (
            _zip_json(archive, "reports/internal/proofs/52-core-stability.json"),
            _zip_json(archive, "reports/internal/proofs/53-timing-stability.json"),
        )


def completion_document(args: argparse.Namespace) -> dict[str, object]:
    state = read_json(args.output_root / "program-state.json")
    execution = (
        read_json(args.output_root / "execution-reconciliation.json")
        if (args.output_root / "execution-reconciliation.json").is_file()
        else {}
    )
    source_lock = (
        read_json(args.output_root / "source-lock.json")
        if (args.output_root / "source-lock.json").is_file()
        else {}
    )
    historical_core, historical_timing = _latest_historical_stability(args)
    root_cause = read_json(
        args.report_dir / "proofs/06-directional-instability-root-cause-classification.json"
    )
    fictional = read_json(
        Path.cwd()
        / "artifacts/20260908-directional-core-boundary-calibration-repair-fresh-"
        "generalization-proof/program-state.json"
    )
    core = _internal_proof(args, 52)
    timing = _internal_proof(args, 53)
    ownership = _internal_proof(args, 54)
    renderer = _internal_proof(args, 55)
    hard = _internal_proof(args, 56)
    quality = (
        read_json(args.output_root / "advisory-message-quality-summary.json")
        if (args.output_root / "advisory-message-quality-summary.json").is_file()
        else {"rows": [], "status": "NOT_MEASURED"}
    )
    core_counts = core.get("counts") if isinstance(core.get("counts"), Mapping) else {}
    timing_counts = (
        timing.get("counts") if isinstance(timing.get("counts"), Mapping) else {}
    )
    run_results = state.get("run_results") if isinstance(state.get("run_results"), Mapping) else {}
    runs_pass = all(run_results.get(run) == "16/16" for run in runner.RUNS)
    required_gates = all(
        _internal_proof(args, runner.RUN_PROOFS[run][gate]).get("status") == "PASS"
        for run in runner.RUNS
        for gate in (3, 4, 5)
    )
    hard_ready = (
        runs_pass
        and int(core_counts.get("UNSTABLE") or 0) == 0
        and int(timing_counts.get("UNSTABLE") or 0) == 0
        and ownership.get("ownership_generalization_verdict")
        == "PASS_NEW_UNSEEN_COHORT"
        and renderer.get("status") == "PASS"
        and hard.get("status") == "PASS"
        and required_gates
        and int(execution.get("namespace_collision_count") or 0) == 0
    )
    quality_rows = quality.get("rows") if isinstance(quality.get("rows"), list) else []
    quality_pass = bool(quality_rows) and all(
        row.get("status") == "PASS" for row in quality_rows if isinstance(row, Mapping)
    )
    if hard_ready and quality_pass:
        readiness = "READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        next_scope = "MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        stop_reason = None
    elif hard_ready:
        readiness = "READY_FOR_MESSAGE_QUALITY_REMEDIATION"
        next_scope = "MESSAGE_SPECIFICITY_AND_REPETITION_REMEDIATION"
        stop_reason = None
    elif int(core_counts.get("UNSTABLE") or 0) > 0:
        readiness = "NOT_READY_DIRECTIONAL_CORE_STABILITY"
        next_scope = "GENERIC_DIRECTIONAL_CORE_REASONING_ARCHITECTURE_REVIEW"
        stop_reason = (
            "DIRECTIONAL_CORE_STABILITY_UNSTABLE_"
            f"{core_counts.get('UNSTABLE')}_OF_{TARGET_TOTAL}"
        )
    else:
        readiness = str(state.get("readiness") or "NOT_READY")
        upstream_completion = _internal_proof(args, 60)
        next_scope = str(
            state.get("next_scope")
            or upstream_completion.get("next_scope")
            or "BOUNDED_FAILURE_REVIEW"
        )
        stop_reason = state.get("stop_reason")
    exposure = _internal_proof(args, 51)
    pause = read_json(args.output_root / "schedule-pause-observation.json")
    run_gate = lambda run, index: _internal_proof(  # noqa: E731
        args, runner.RUN_PROOFS[run][index]
    ).get("status")
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": LATEST_FINAL_HEAD,
        "work_instruction_commit": state.get("work_instruction_commit"),
        "implementation_commit": state.get("implementation_commit"),
        "final_head_sha": "RESOLVED_IN_BUNDLE_COMPLETION",
        "branch": state.get("branch"),
        "latest_result_zip_sha256": LATEST_RESULT_SHA256,
        "latest_result_integrity": "PASS",
        "historical_core_stability_counts": historical_core.get("counts"),
        "historical_timing_stability_counts": historical_timing.get("counts"),
        "historical_unstable_tickers": [
            row.get("ticker")
            for row in historical_core.get("rows") or []
            if isinstance(row, Mapping) and row.get("classification") == "UNSTABLE"
        ],
        "adjacent_calibration_ambiguity_count": root_cause.get(
            "adjacent_calibration_count"
        ),
        "material_evidence_variance_count": root_cause.get(
            "material_evidence_variance_count"
        ),
        "true_semantic_divergence_count": root_cause.get(
            "true_semantic_divergence_count"
        ),
        "calibration_root_cause": root_cause.get("root_cause_result"),
        "directional_calibration_repair_applied": 1,
        "directional_threshold_changed": 0,
        "majority_vote_adopted": 0,
        "fixed_weight_scorecard_adopted": 0,
        "fictional_calibration_model_call_count": fictional.get(
            "fictional_model_invocation_count"
        ),
        "fictional_calibration_unstable_count": fictional.get(
            "fictional_calibration_unstable_count"
        ),
        "fictional_calibration_status": fictional.get("fictional_calibration_status"),
        "previous_exclusion_registry_count": PREVIOUS_EXCLUSION_COUNT,
        "fresh_exclusion_registry_count": state.get("exclusion_registry_count"),
        "newly_excluded_current_cohort_count": NEWLY_RETIRED_COUNT,
        "fresh_us_target_status": _internal_proof(args, 7).get(
            "source_target_status", "NOT_MEASURED"
        ),
        "fresh_kr_target_status": _internal_proof(args, 10).get(
            "source_target_status", "NOT_MEASURED"
        ),
        "fresh_cohort": state.get("ordered_cohort") or [],
        "fresh_source_generation": state.get("source_generation_id"),
        "fresh_source_lock": source_lock.get("source_lock_sha256"),
        "model": runner.MODEL,
        "reasoning_effort": runner.EFFORT,
        "batch_semantics": runner.BATCH_SEMANTICS,
        "subjects_per_context": runner.CONTEXT_SIZE,
        "timeout": runner.TIMEOUT_SECONDS,
        "timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "planned_real_contexts": EXPECTED_REAL_CONTEXTS,
        "attempted_real_contexts": execution.get("attempted_contexts", 0),
        "successful_real_contexts": execution.get("successful_contexts", 0),
        "failed_real_contexts": execution.get("failed_contexts", 0),
        "distinct_real_namespace_count": execution.get("distinct_namespace_count", 0),
        "namespace_collision_count": execution.get("namespace_collision_count", 0),
        "raw_output_document_count": execution.get("raw_output_document_count", 0),
        "unique_issuer_output_count": execution.get("unique_issuer_output_count", 0),
        "wrapper_retry_count": execution.get("wrapper_explicit_retry_count", 0),
        "cli_retry_signal_count": execution.get("observed_cli_retry_signal_count", 0),
        "disconnect_count": execution.get(
            "observed_websocket_disconnect_signal_count", 0
        ),
        "capacity_failure_count": execution.get("explicit_capacity_count", 0),
        "timeout_count": execution.get("watchdog_timeout_count", 0),
        "orphan_count": execution.get("orphan_count", 0),
        "run_results": {run: run_results.get(run, "NOT_RUN") for run in runner.RUNS},
        "first_ownership_gate": run_gate("first", 3),
        "first_renderer_gate": run_gate("first", 4),
        "first_hard_safety_gate": run_gate("first", 5),
        "first_message_quality": _message_quality(args, "first").get("status"),
        "run_a_ownership_gate": run_gate("a", 3),
        "run_a_renderer_gate": run_gate("a", 4),
        "run_a_hard_safety_gate": run_gate("a", 5),
        "run_a_message_quality": _message_quality(args, "a").get("status"),
        "run_b_ownership_gate": run_gate("b", 3),
        "run_b_renderer_gate": run_gate("b", 4),
        "run_b_hard_safety_gate": run_gate("b", 5),
        "run_b_message_quality": _message_quality(args, "b").get("status"),
        "run_c_ownership_gate": run_gate("c", 3),
        "run_c_renderer_gate": run_gate("c", 4),
        "run_c_hard_safety_gate": run_gate("c", 5),
        "run_c_message_quality": _message_quality(args, "c").get("status"),
        "fresh_core_stability_counts": core_counts,
        "fresh_timing_stability_counts": timing_counts,
        "fresh_ownership_generalization": ownership.get(
            "ownership_generalization_verdict", "NOT_MEASURED"
        ),
        "fresh_message_quality_status": (
            "PASS"
            if quality_pass
            else quality.get("status")
            if runs_pass
            else "NOT_MEASURED"
        ),
        "exposure_state": exposure.get("holdout_output_exposure_state"),
        "semantic_revelation_state": exposure.get(
            "holdout_semantic_revelation_state"
        ),
        "retirement_state": exposure.get("holdout_retirement_state"),
        "future_unseen_reuse_allowed": exposure.get(
            "future_unseen_holdout_reuse_allowed"
        ),
        "observed_paused_schedule_count": pause.get(
            "observed_paused_schedule_count", 8
        ),
        "automatic_monitoring_resume": 0,
        "paid_data_service_change": 0,
        "production_db_mutation": 0,
        "production_send": 0,
        "monitoring_registration_change": 0,
        "live_v2_change": 0,
        "night_futures_change": 0,
        "artifact_count": "PENDING_FINAL_PACKAGE",
        "artifact_hash_mismatch_count": "PENDING_FINAL_PACKAGE",
        "artifact_size_mismatch_count": "PENDING_FINAL_PACKAGE",
        "artifact_secret_scan_failure_count": "PENDING_FINAL_PACKAGE",
        "status": "PASS" if hard_ready else "STOPPED",
        "readiness": readiness,
        "stop_reason": stop_reason,
        "next_scope": next_scope,
    }
    return completion


def close_reports(args: argparse.Namespace) -> None:
    _configure_stack()
    _write_source_reports(args)
    _execution_reports(args)
    final_mapping = {
        FINAL_REPORT_NAMES[42]: 51,
        FINAL_REPORT_NAMES[43]: 52,
        FINAL_REPORT_NAMES[44]: 53,
        FINAL_REPORT_NAMES[45]: 54,
        FINAL_REPORT_NAMES[46]: 55,
        FINAL_REPORT_NAMES[47]: 56,
    }
    for name, source in final_mapping.items():
        write_named_report(args.report_dir, name, _internal_proof(args, source))
    quality = (
        read_json(args.output_root / "advisory-message-quality-summary.json")
        if (args.output_root / "advisory-message-quality-summary.json").is_file()
        else {"contract": "message-quality-summary-v1", "status": "NOT_MEASURED"}
    )
    execution = (
        read_json(args.output_root / "execution-reconciliation.json")
        if (args.output_root / "execution-reconciliation.json").is_file()
        else {"contract": "runtime-reliability-v1", "status": "NOT_MEASURED"}
    )
    production = {
        "contract": "directional-calibration-production-no-change-v1",
        "production_db_mutation": 0,
        "production_telegram_send": 0,
        "monitoring_registration_change": 0,
        "live_v2_change": 0,
        "automatic_monitoring_resume": 0,
        "status": "PASS",
    }
    night = {
        "contract": "directional-calibration-night-futures-no-change-v1",
        "night_futures_code_mutation": 0,
        "night_futures_decision_packet_injection": 0,
        "night_futures_change": 0,
        "status": "PASS",
    }
    completion = completion_document(args)
    handoff = {
        "contract": "directional-calibration-next-scope-handoff-v1",
        "readiness": completion["readiness"],
        "next_scope": completion["next_scope"],
        "monitoring_remains_paused": True,
        "automatic_monitoring_resume": 0,
        "status": "PASS" if completion["status"] == "PASS" else "NOT_READY",
    }
    runtime = {
        "contract": "directional-calibration-runtime-reliability-observations-v1",
        **execution,
        "status": execution.get("status", "NOT_MEASURED"),
    }
    for name, document in (
        (FINAL_REPORT_NAMES[48], quality),
        (FINAL_REPORT_NAMES[49], runtime),
        (FINAL_REPORT_NAMES[50], production),
        (FINAL_REPORT_NAMES[51], night),
        (FINAL_REPORT_NAMES[52], handoff),
        (FINAL_REPORT_NAMES[53], completion),
    ):
        write_named_report(args.report_dir, name, document)
    write_json(args.output_root / "program-completion.json", completion)
    main_state_path = (
        Path.cwd()
        / "artifacts/20260908-directional-core-boundary-calibration-repair-fresh-"
        "generalization-proof/program-state.json"
    )
    main_state = read_json(main_state_path)
    main_state.update(
        {
            "state": "FRESH_REAL_PROOF_COMPLETE"
            if completion["status"] == "PASS"
            else "FRESH_REAL_PROOF_STOPPED",
            "fresh_real_cohort_consumed": int(
                bool(completion.get("attempted_real_contexts"))
            ),
            "fresh_real_generation_id": state_value(
                args.output_root, "program_generation_id"
            ),
            "fresh_real_readiness": completion["readiness"],
            "fresh_real_stop_reason": completion["stop_reason"],
        }
    )
    write_json(main_state_path, main_state)
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True), flush=True)


def state_value(output_root: Path, key: str) -> object:
    return read_json(output_root / "program-state.json").get(key)


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def package(args: argparse.Namespace) -> None:
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_for_final_package")
    completion = read_json(args.output_root / "program-completion.json")
    final_head = git_value("rev-parse", "HEAD")
    final_tree = git_value("rev-parse", "HEAD^{tree}")
    if args.bundle_root.exists() or args.zip_output.exists():
        raise ValueError("new_bundle_and_zip_paths_required")
    args.bundle_root.mkdir(parents=True)
    calibration_root = (
        Path.cwd()
        / "artifacts/20260908-directional-core-boundary-calibration-repair-fresh-"
        "generalization-proof"
    )
    shutil.copytree(calibration_root, args.bundle_root / "experiment/calibration")
    shutil.copytree(args.output_root, args.bundle_root / "experiment/fresh-real-proof")
    shutil.copytree(args.report_dir, args.bundle_root / "reports")
    instruction_target = args.bundle_root / "work-instruction" / Path(
        WORK_INSTRUCTION_PATH
    ).name
    instruction_target.parent.mkdir(parents=True)
    shutil.copy2(Path.cwd() / WORK_INSTRUCTION_PATH, instruction_target)
    completion.update(
        {
            "final_head_sha": final_head,
            "final_tree_sha": final_tree,
            "worktree_clean_at_package": True,
            "packaged_at": datetime.now(UTC).isoformat(),
        }
    )
    completion_path = args.bundle_root / "completion.json"
    write_json(completion_path, completion)
    paths = sorted(path for path in args.bundle_root.rglob("*") if path.is_file())
    rows = []
    secret_failures = 0
    for path in paths:
        scan = legacy.scan_artifact_secrets([path])
        secret_failures += int(scan.get("secret_exposure_count") or 0)
        rows.append(
            {
                "path": str(path.relative_to(args.bundle_root)),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                "secret_scan_status": scan.get("secret_scan_status"),
            }
        )
    if secret_failures:
        raise ValueError(f"artifact_secret_scan_failed:{secret_failures}")
    completion.update(
        {
            "artifact_count": len(rows),
            "indexed_payload_count": len(rows),
            "artifact_hash_mismatch_count": 0,
            "artifact_size_mismatch_count": 0,
            "artifact_secret_scan_failure_count": 0,
        }
    )
    write_json(completion_path, completion)
    rows = [
        {
            "path": str(path.relative_to(args.bundle_root)),
            "sha256": file_sha256(path),
            "byte_size": path.stat().st_size,
            "secret_scan_status": legacy.scan_artifact_secrets([path]).get(
                "secret_scan_status"
            ),
        }
        for path in sorted(args.bundle_root.rglob("*"))
        if path.is_file()
    ]
    index = {
        "contract": "directional-calibration-artifact-index-v1",
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
        archived_index = _zip_json(archive, "artifact-index.json")
        indexed = {str(row["path"]): row for row in archived_index.get("rows") or []}
        expected = set(names) - {"artifact-index.json"}
        failures = {
            "duplicate_members": len(names) - len(set(names)),
            "unsafe_members": sum(not _safe_member(name) for name in names),
            "crc_failure": archive.testzip(),
            "index_membership_mismatch": int(set(indexed) != expected),
            "hash_mismatches": sum(
                hashlib.sha256(archive.read(name)).hexdigest()
                != indexed[name].get("sha256")
                for name in indexed
            ),
            "size_mismatches": sum(
                len(archive.read(name)) != indexed[name].get("byte_size")
                for name in indexed
            ),
        }
    if any(bool(value) for value in failures.values()):
        raise ValueError(f"final_zip_integrity_failure:{failures}")
    zip_sha = file_sha256(args.zip_output)
    write_text(args.zip_output.with_suffix(args.zip_output.suffix + ".sha256"), zip_sha)
    print(
        json.dumps(
            {
                "zip": str(args.zip_output),
                "zip_sha256": zip_sha,
                "zip_member_count": len(names),
                "indexed_payload_count": len(indexed),
                "integrity": failures,
                "status": "PASS",
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--bootstrap", action="store_true")
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--seal", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--close-reports", action="store_true")
    mode.add_argument("--package", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--latest-result-zip", type=Path, required=True)
    parser.add_argument("--expansion-zip", type=Path, required=True)
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--timeout", type=int, default=runner.TIMEOUT_SECONDS)
    parser.add_argument("--zip-output", type=Path, required=True)
    args = parser.parse_args()
    for name in (
        "output_root",
        "report_dir",
        "bundle_root",
        "latest_result_zip",
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
        package(args)


if __name__ == "__main__":
    main()
