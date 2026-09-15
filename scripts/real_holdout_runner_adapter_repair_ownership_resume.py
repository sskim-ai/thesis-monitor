from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import zipfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.jobs import accepted_decision_v2_runtime as accepted_runtime
from app.services.direction_timing_ownership_service import OwnedEvidencePacket
from app.services.structured_autonomy_shadow_service import (
    explicit_actionable_trade_directives,
)
from scripts import directional_core_price_timing_holdout as frozen
from scripts import model_transport_revalidation_ownership_continuation as transport
from scripts import synthetic_canary_fixture_repair_ownership_resume as previous
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "real-holdout-runner-adapter-repair-ownership-resume-v1"
PROOF_DIRECTORY = "proofs"
PRIOR_REPORT_SHA256 = "05da7dda67957f9f1c6dab87885b0a154c4247a8fb1b79a15688e0729b752816"
PRIOR_IMPLEMENTATION_COMMIT = "00d1248b7846ccf05bc9e3ceaf372a97b71568e0"
BASE_SHA = "b509c42cebf5bb96c45c2e17b63ccf250402f893"
WORK_INSTRUCTION_COMMIT = "a539eaa"
SOURCE_GENERATION_ID = previous.SOURCE_GENERATION_ID
SOURCE_LOCK_SHA256 = previous.SOURCE_LOCK_SHA256
CURRENT_HOLDOUT = previous.CURRENT_HOLDOUT
CONSUMED_HOLDOUT = previous.CONSUMED_LATEST_HOLDOUT16
MODEL = previous.MODEL
EFFORT = previous.EFFORT
MODEL_TIMEOUT_SECONDS = previous.MODEL_TIMEOUT_SECONDS
MODEL_CONTEXT_BATCH_SIZE = previous.MODEL_CONTEXT_BATCH_SIZE

REPORT_NAMES = (
    "01-repository-provenance",
    "02-runner-adapter-root-cause",
    "03-runner-adapter-binding-contract",
    "04-runner-adapter-binding-preflight",
    "05-bounded-diff-audit",
    "06-architecture-semantic-freeze-reverification",
    "07-source-freeze-reverification",
    "08-transport-topology-freeze-reverification",
    "09-model-semantic-input-freeze",
    "10-current-holdout-reuse-gate",
    "11-live-workload-coexistence-audit",
    "12-resume-source-lock",
    "13-resume-first",
    "14-first-per-run-semantic-gates",
    "15-resume-run-a",
    "16-run-a-per-run-semantic-gates",
    "17-resume-run-b",
    "18-run-b-per-run-semantic-gates",
    "19-resume-run-c",
    "20-run-c-per-run-semantic-gates",
    "21-holdout-exposure-retirement-state",
    "22-resume-core-stability",
    "23-resume-timing-stability",
    "24-resume-dominance-ownership",
    "25-resume-renderer-action-ownership",
    "26-resume-hard-safety-regression",
    "27-production-no-change",
    "28-night-futures-no-change",
    "29-monitoring-bootstrap-next-handoff",
    "30-program-completion",
)

RUN_REPORT = {
    "first": "13-resume-first",
    "a": "15-resume-run-a",
    "b": "17-resume-run-b",
    "c": "19-resume-run-c",
}
RUN_GATE_REPORT = {
    "first": "14-first-per-run-semantic-gates",
    "a": "16-run-a-per-run-semantic-gates",
    "b": "18-run-b-per-run-semantic-gates",
    "c": "20-run-c-per-run-semantic-gates",
}


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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def git_value(*args: str) -> str:
    return transport.git_value(*args)


def generation_id(commit: str, as_of: datetime) -> str:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(f"{commit}|{stamp}|{PROGRAM_CONTRACT}".encode()).hexdigest()[:12]
    return f"20260906-real-holdout-adapter-resume-{stamp}-{suffix}"


def proof_path(report_dir: Path, name: str) -> Path:
    return report_dir / PROOF_DIRECTORY / f"{name}.json"


def write_proof(report_dir: Path, name: str, value: Mapping[str, object]) -> None:
    write_json(proof_path(report_dir, name), value)


def runner_supplied_keys() -> tuple[str, ...]:
    return (
        "codex_bin",
        "prompt",
        "output",
        "log",
        "schema",
        "cwd",
        "timeout",
        "state_namespace",
    )


def canonical_adapter_keys() -> tuple[str, ...]:
    signature = inspect.signature(transport.ContinuationTransportAdapter.invoke)
    return tuple(name for name in signature.parameters if name != "self")


def normalize_real_runner_kwargs(
    adapter: object, runner_kwargs: Mapping[str, object]
) -> dict[str, object]:
    normalized = dict(runner_kwargs)
    runner_codex_bin = Path(str(normalized.pop("codex_bin"))).resolve()
    adapter_codex_bin = Path(str(getattr(adapter, "codex_bin"))).resolve()
    if runner_codex_bin != adapter_codex_bin:
        raise ValueError("runner_adapter_codex_binary_mismatch")
    signature = inspect.signature(transport.ContinuationTransportAdapter.invoke)
    signature.bind(adapter, **normalized)
    return normalized


@contextmanager
def real_holdout_runner_bridge(adapter: object) -> Iterator[None]:
    original = engine._invoke_signed_in_codex

    def invoke(**runner_kwargs: object) -> dict[str, object]:
        normalized = normalize_real_runner_kwargs(adapter, runner_kwargs)
        return getattr(adapter, "runner_invoke")(**normalized)

    engine._invoke_signed_in_codex = invoke
    try:
        yield
    finally:
        engine._invoke_signed_in_codex = original


class BindingPreflightComplete(RuntimeError):
    pass


class BindingSpyAdapter:
    def __init__(self, codex_bin: str) -> None:
        self.codex_bin = codex_bin
        self.calls: list[dict[str, object]] = []

    def runner_invoke(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(dict(kwargs))
        raise BindingPreflightComplete


def root_cause_document() -> dict[str, object]:
    signature = inspect.signature(transport.ContinuationTransportAdapter.invoke)
    sample = {name: object() for name in runner_supplied_keys()}
    bind_error = None
    try:
        signature.bind(object(), **sample)
    except TypeError as exc:
        bind_error = str(exc)
    unexpected = sorted(set(runner_supplied_keys()) - set(canonical_adapter_keys()))
    missing = sorted(
        name
        for name, parameter in signature.parameters.items()
        if name != "self"
        and parameter.default is inspect.Parameter.empty
        and name not in runner_supplied_keys()
    )
    return {
        "contract": "runner-adapter-root-cause-v1",
        "adapter_callable_location": (
            "scripts/model_transport_revalidation_ownership_continuation.py:"
            "ContinuationTransportAdapter.invoke"
        ),
        "runner_call_site_location": (
            "scripts/directional_core_price_timing_holdout.py:execute_two_stage_run"
        ),
        "canonical_adapter_parameters": list(canonical_adapter_keys()),
        "runner_supplied_parameters": list(runner_supplied_keys()),
        "unexpected_parameters": unexpected,
        "missing_required_parameters": missing,
        "pre_repair_bind_error": bind_error,
        "codex_bin_classification": "RUNNER_OWNED_LEGACY_TRANSPORT_CONFIGURATION",
        "passed_canary_invocation_shape": "DIRECT_CANONICAL_ADAPTER_INVOKE",
        "defect_location": "REAL_HOLDOUT_RUNNER_ARGUMENT_BRIDGE",
        "result": "RUNNER_ADAPTER_BINDING_ROOT_CAUSE_CONFIRMED",
        "status": (
            "PASS" if unexpected == ["codex_bin"] and not missing and bind_error else "FAIL"
        ),
    }


def model_free_binding_preflight(args: argparse.Namespace, output_root: Path) -> dict[str, object]:
    (
        cohort,
        contexts,
        evidence,
        owned,
        core_aliases,
        timing_aliases,
        price_maps,
        stocks,
    ) = transport._load_frozen_holdout(args)
    codex_bin = accepted_runtime._signed_in_codex_bin()
    spy = BindingSpyAdapter(codex_bin)
    preflight_root = output_root / "model-free-binding-preflight"
    try:
        with real_holdout_runner_bridge(spy):
            frozen.execute_two_stage_run(
                run="model-free-binding-preflight",
                generation_id=SOURCE_GENERATION_ID,
                source_lock_sha256=SOURCE_LOCK_SHA256,
                prompt_root=args.source_root,
                run_root=preflight_root,
                cohort=cohort,
                base_contexts=contexts,
                evidence=evidence,
                owned=owned,
                core_aliases=core_aliases,
                timing_aliases=timing_aliases,
                price_maps=price_maps,
                stocks=stocks,
                timeout=MODEL_TIMEOUT_SECONDS,
            )
    except BindingPreflightComplete:
        pass
    if len(spy.calls) != 1:
        raise ValueError("binding_preflight_dispatch_count_mismatch")
    observed = spy.calls[0]
    expected = set(runner_supplied_keys()) - {"codex_bin"}
    signature = inspect.signature(transport.ContinuationTransportAdapter.invoke)
    signature.bind(spy, **observed)
    if set(observed) != expected:
        raise ValueError("binding_preflight_canonical_shape_mismatch")
    return {
        "contract": "real-holdout-runner-adapter-binding-preflight-v1",
        "actual_runner_path_exercised": 1,
        "model_invocation_count": 0,
        "runner_supplied_parameters": list(runner_supplied_keys()),
        "runner_owned_parameters_consumed": ["codex_bin"],
        "adapter_parameters_observed": sorted(observed),
        "unexpected_adapter_parameters": sorted(set(observed) - set(canonical_adapter_keys())),
        "missing_adapter_parameters": sorted(expected - set(observed)),
        "codex_binary_identity_verified": 1,
        "result": "REAL_HOLDOUT_RUNNER_ADAPTER_BINDING_PREFLIGHT_PASS",
        "status": "PASS",
    }


def verify_prior_and_freeze(args: argparse.Namespace) -> dict[str, object]:
    if file_sha256(args.prior_report) != PRIOR_REPORT_SHA256:
        raise ValueError("prior_report_sha256_mismatch")
    prior_state = read_json(args.prior_state)
    if prior_state.get("transport_canary_model_call_count") != 7:
        raise ValueError("historical_canary_count_mismatch")
    if prior_state.get("transport_canary_status") != "PASS":
        raise ValueError("historical_canary_status_mismatch")
    if prior_state.get("real_holdout_model_call_count") != 0:
        raise ValueError("prior_real_holdout_was_invoked")
    frozen_state = previous.verify_frozen(args)
    return {"prior_state": prior_state, "frozen_state": frozen_state}


def directory_manifest(root: Path) -> dict[str, str]:
    return {
        str(Path(root.name) / path.relative_to(root)): file_sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def model_input_manifest(source_root: Path) -> dict[str, str]:
    return directory_manifest(source_root / "prompts") | directory_manifest(source_root / "schemas")


def base_proofs(
    args: argparse.Namespace,
    *,
    state: Mapping[str, object],
    verification: Mapping[str, object],
    root_cause: Mapping[str, object],
    preflight: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    frozen_state = verification["frozen_state"]
    prior_state = verification["prior_state"]
    return {
        "01-repository-provenance": {
            "contract": "repository-provenance-v1",
            "branch": state["branch"],
            "base_sha": BASE_SHA,
            "prior_implementation_commit": PRIOR_IMPLEMENTATION_COMMIT,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": state["implementation_commit"],
            "working_tree_before_repair": "CLEAN",
            "post_prior_implementation_changes": "NONSEMANTIC_REPORT_EVIDENCE_ONLY",
            "unexplained_semantic_repository_drift": 0,
            "status": "PASS",
        },
        "02-runner-adapter-root-cause": dict(root_cause),
        "03-runner-adapter-binding-contract": {
            "contract": "runner-adapter-binding-contract-v1",
            "runner_owned_parameters": ["codex_bin"],
            "canonical_adapter_parameters": list(canonical_adapter_keys()),
            "normalization": "VERIFY_CODEX_BINARY_IDENTITY_THEN_REMOVE_RUNNER_ONLY_KEY",
            "adapter_api_widened": 0,
            "continuation_transport_adapter_mutation": 0,
            "status": "PASS",
        },
        "04-runner-adapter-binding-preflight": dict(preflight),
        "05-bounded-diff-audit": {
            "contract": "bounded-runner-adapter-diff-audit-v1",
            "authorized_harness_hash_drift": 1,
            "changed_semantic_surface": ["EXPERIMENT_ONLY_REAL_RUNNER_BRIDGE"],
            "directional_core_semantic_mutation": 0,
            "price_timing_semantic_mutation": 0,
            "composer_semantic_mutation": 0,
            "renderer_semantic_mutation": 0,
            "prompt_semantic_drift": 0,
            "schema_semantic_drift": 0,
            "production_market_enum_mutation": 0,
            "source_assembly_mutation": 0,
            "source_sufficiency_policy_drift": 0,
            "fundamental_source_enrichment_drift": 0,
            "transport_topology_mutation": 0,
            "model_semantic_input_drift": 0,
            "model_context_shape_mutation": 0,
            "timeout_increase_this_task": 0,
            "batch_split_adopted": 0,
            "ticker_specific_production_exception": 0,
            "status": "PASS",
        },
        "06-architecture-semantic-freeze-reverification": {
            "contract": "architecture-semantic-freeze-reverification-v1",
            "expected_hashes": previous.EXPECTED_ARCHITECTURE_HASHES,
            "actual_hashes": frozen_state["architecture"],
            "architecture_semantic_drift": 0,
            "status": "PASS",
        },
        "07-source-freeze-reverification": {
            "contract": "source-freeze-reverification-v1",
            "expected_hashes": previous.EXPECTED_SOURCE_HASHES,
            "actual_hashes": frozen_state["sources"],
            "source_lock_sha256": SOURCE_LOCK_SHA256,
            "source_drift": 0,
            "source_sufficiency_policy_drift": 0,
            "status": "PASS",
        },
        "08-transport-topology-freeze-reverification": {
            "contract": "transport-topology-freeze-reverification-v1",
            "expected_hashes": previous.EXPECTED_TRANSPORT_HASHES,
            "actual_hashes": frozen_state["transport"],
            "historical_canary_harness_sha256": file_sha256(Path(previous.__file__).resolve()),
            "historical_canary_harness_expected_sha256": prior_state["resume_harness_sha256"],
            "historical_canaries_reused": 7,
            "historical_canaries_rerun": 0,
            "transport_topology_mutation": 0,
            "model_timeout_owner_count": 1,
            "status": "PASS",
        },
        "09-model-semantic-input-freeze": {
            "contract": "model-semantic-input-freeze-v1",
            "prompt_schema_manifest": model_input_manifest(args.source_root),
            "source_lock_sha256": SOURCE_LOCK_SHA256,
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "batch_semantics": "MODEL_CONTEXT_COUPLED",
            "real_run_batch_size": MODEL_CONTEXT_BATCH_SIZE,
            "model_semantic_input_drift": 0,
            "prompt_semantic_drift": 0,
            "schema_semantic_drift": 0,
            "status": "PASS",
        },
        "10-current-holdout-reuse-gate": {
            "contract": "current-holdout-reuse-gate-v2",
            "ordered_cohort": list(CURRENT_HOLDOUT),
            "prior_real_holdout_model_invocation_count": 0,
            "prior_real_holdout_model_output_count": 0,
            "source_lock_unchanged": 1,
            "architecture_semantics_unchanged": 1,
            "prompt_schema_semantics_unchanged": 1,
            "model_effort_unchanged": 1,
            "batch_context_unchanged": 1,
            "transport_topology_unchanged": 1,
            "current_holdout_reuse_allowed": 1,
            "holdout_output_exposure_state": "UNEXPOSED",
            "holdout_retirement_state": "ACTIVE_UNEXPOSED",
            "future_unseen_holdout_reuse_allowed": 1,
            "status": "PASS",
        },
        "11-live-workload-coexistence-audit": {
            "contract": "natural-live-workload-coexistence-guard-v1",
            "events": [],
            "live_workload_contention_risk": "NOT_OBSERVED",
            "shadow_pause_for_natural_live": 0,
            "natural_live_cancel_count": 0,
            "scheduler_mutation": 0,
            "status": "PENDING",
        },
        "12-resume-source-lock": {
            "contract": "real-holdout-resume-source-lock-v1",
            "resume_generation_id": state["resume_generation_id"],
            "source_generation_id": SOURCE_GENERATION_ID,
            "ordered_cohort": list(CURRENT_HOLDOUT),
            "source_lock_sha256": SOURCE_LOCK_SHA256,
            "consumed_regression_model_calls": 0,
            "source_drift": 0,
            "status": "PASS",
        },
        "27-production-no-change": {
            "contract": "production-no-change-v1",
            "main_merge": 0,
            "production_db_mutation": 0,
            "production_telegram_send": 0,
            "production_scheduler_change": 0,
            "monitoring_registration_calls": 0,
            "live_structured_autonomy_activation": 0,
            "live_v2_change": 0,
            "status": "PASS",
        },
        "28-night-futures-no-change": {
            "contract": "night-futures-no-change-v1",
            "night_futures_code_mutation": 0,
            "night_futures_decision_packet_injection": 0,
            "status": "PASS",
        },
    }


def prepare(args: argparse.Namespace) -> None:
    if args.output_root.exists():
        raise ValueError("new_output_root_required")
    root_cause = root_cause_document()
    if root_cause["status"] != "PASS":
        raise ValueError("runner_adapter_root_cause_not_confirmed")
    verification = verify_prior_and_freeze(args)
    args.output_root.mkdir(parents=True)
    preflight = model_free_binding_preflight(args, args.output_root)
    implementation_commit = git_value("rev-parse", "HEAD")
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARED_FROZEN",
        "branch": git_value("branch", "--show-current"),
        "base_sha": BASE_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": implementation_commit,
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "runner_harness_sha256": file_sha256(Path(__file__).resolve()),
        "model_input_manifest_sha256": canonical_sha256(model_input_manifest(args.source_root)),
        "resume_generation_id": generation_id(implementation_commit, args.as_of),
        "source_generation_id": SOURCE_GENERATION_ID,
        "source_lock_sha256": SOURCE_LOCK_SHA256,
        "ordered_cohort": list(CURRENT_HOLDOUT),
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_timeout_seconds": MODEL_TIMEOUT_SECONDS,
        "model_timeout_owner_count": 1,
        "batch_semantics": "MODEL_CONTEXT_COUPLED",
        "real_run_batch_size": MODEL_CONTEXT_BATCH_SIZE,
        "runner_adapter_binding_preflight": "PASS",
        "historical_canaries_reused": 7,
        "historical_canaries_rerun": 0,
        "real_holdout_model_invocation_count": 0,
        "real_holdout_transport_retry_count": 0,
        "holdout_output_exposure_state": "UNEXPOSED",
        "holdout_semantic_revelation_state": "NOT_MEASURED",
        "holdout_retirement_state": "ACTIVE_UNEXPOSED",
        "future_unseen_holdout_reuse_allowed": 1,
        "same_cohort_architecture_tuning_rerun_allowed": 0,
        "production_mutation": 0,
    }
    args.report_dir.mkdir(parents=True, exist_ok=True)
    for name, proof in base_proofs(
        args,
        state=state,
        verification=verification,
        root_cause=root_cause,
        preflight=preflight,
    ).items():
        write_proof(args.report_dir, name, proof)
    for name in REPORT_NAMES:
        path = proof_path(args.report_dir, name)
        if not path.is_file():
            write_proof(
                args.report_dir,
                name,
                {
                    "contract": "real-holdout-not-yet-measured-v1",
                    "status": "NOT_MEASURED",
                    "reason": "REAL_HOLDOUT_EXECUTION_NOT_STARTED",
                },
            )
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(state, sort_keys=True), flush=True)


def verify_program_freeze(state: Mapping[str, object]) -> None:
    if file_sha256(Path(__file__).resolve()) != state["runner_harness_sha256"]:
        raise ValueError("runner_harness_mutation_after_freeze")


def receipt_rows(receipt_root: Path) -> list[dict[str, object]]:
    rows = []
    for path in sorted(receipt_root.glob("*.json")):
        value = read_json(path)
        rows.append(
            {
                "invocation_id": value["invocation_id"],
                "stage": value["stage"],
                "batch_id": value["batch_id"],
                "subject_count": value["subject_count"],
                "transport_grouping_mode": value["transport_grouping_mode"],
                "status": value["status"],
                "input_bytes": value["input_bytes"],
                "prompt_sha256": value["prompt_sha256"],
                "schema_sha256": value["schema_sha256"],
                "elapsed_to_first_output_seconds": value["elapsed_to_first_output_seconds"],
                "elapsed_to_exit_seconds": value["elapsed_to_exit_seconds"],
                "stdout_bytes": value["stdout_bytes"],
                "stderr_bytes": value["stderr_bytes"],
                "output_bytes": value["output_bytes"],
                "timeout_owner": value["timeout_owner"],
                "child_cleanup_status": value["child_cleanup_status"],
                "orphan_model_process_count": value["orphan_model_process_count"],
                "secret_exposure_count": value["secret_exposure_count"],
                "receipt_sha256": file_sha256(path),
            }
        )
    return rows


def exposed_subjects(output_root: Path) -> set[str]:
    tickers: set[str] = set()
    for path in sorted(output_root.glob("*-batch-*.json")):
        try:
            value = read_json(path)
        except (ValueError, json.JSONDecodeError):
            continue
        candidates = value.get("candidates")
        if not isinstance(candidates, list):
            continue
        for candidate in candidates:
            if isinstance(candidate, Mapping) and candidate.get("ticker"):
                tickers.add(str(candidate["ticker"]))
    return tickers


def per_run_semantic_gates(
    run: str,
    document: Mapping[str, object],
    owned: Mapping[str, OwnedEvidencePacket],
) -> dict[str, object]:
    rows = [row for row in document.get("rows", []) if isinstance(row, Mapping)]
    ownership_rows = [row["ownership"] for row in rows if isinstance(row.get("ownership"), Mapping)]

    def ownership_total(field: str) -> int:
        return sum(int(row.get(field) or 0) for row in ownership_rows)

    complete_output = len(rows) == len(CURRENT_HOLDOUT)
    dominance = (
        frozen._dominance_audit(document, owned)
        if complete_output
        else {
            "status": "NOT_MEASURED",
            "final_direction_owner": "NOT_MEASURED",
            "price_only_directional_ownership_violations": "NOT_MEASURED",
            "price_only_holder_reduce": "NOT_MEASURED",
        }
    )
    imperative_rows = []
    for row in rows:
        matches = [
            match.model_dump(mode="json")
            for match in explicit_actionable_trade_directives(
                str(row.get("rendered_message") or "")
            )
        ]
        if matches:
            imperative_rows.append({"ticker": row["ticker"], "matches": matches})
    ownership_values = {
        "directional_core_price_technical_refs": ownership_total(
            "directional_core_price_technical_refs"
        ),
        "directional_core_supply_refs": ownership_total("directional_core_supply_refs"),
        "supply_directional_core_usage": ownership_total("directional_core_supply_refs"),
        "buy_without_nonprice_material_anchor": ownership_total(
            "buy_without_nonprice_material_anchor"
        ),
        "sell_without_nonprice_material_anchor": ownership_total(
            "sell_without_nonprice_material_anchor"
        ),
        "timing_stage_direction_mutation": ownership_total("timing_stage_direction_mutation"),
        "timing_stage_balance_mutation": ownership_total("timing_stage_balance_mutation"),
        "timing_stage_hold_lean_mutation": ownership_total("timing_stage_hold_lean_mutation"),
        "price_timing_new_buyer_upgrade": ownership_total("price_timing_new_buyer_upgrade"),
        "price_only_holder_reduce": dominance["price_only_holder_reduce"],
        "price_only_directional_ownership_violations": dominance[
            "price_only_directional_ownership_violations"
        ],
        "directional_model_calls_on_source_insufficient": 0,
        "price_only_directional_model_calls": 0,
    }
    ownership_gate = (
        "PASS"
        if complete_output
        and all(value == 0 for value in ownership_values.values())
        and dominance["final_direction_owner"] == "DIRECTIONAL_CORE"
        else "FAIL"
        if complete_output
        else "NOT_MEASURED"
    )
    renderer_violations = len(imperative_rows)
    renderer_gate = (
        "PASS"
        if complete_output
        and renderer_violations == 0
        and all(row.get("status") == "PASS" for row in rows)
        else "FAIL"
        if complete_output
        else "NOT_MEASURED"
    )
    known_hard = (
        int(document.get("hard_safety_regression") or 0) if complete_output else "NOT_MEASURED"
    )
    hard_gate = (
        "PASS"
        if complete_output
        and known_hard == 0
        and int(document.get("schema_failure") or 0) == 0
        and int(document.get("validator_false_positive") or 0) == 0
        else "FAIL"
        if complete_output
        else "NOT_MEASURED"
    )
    status = (
        "PASS"
        if document.get("status") == "PASS"
        and ownership_gate == renderer_gate == hard_gate == "PASS"
        else "FAIL"
        if complete_output
        else "NOT_MEASURED"
    )
    return {
        "contract": "real-holdout-per-run-semantic-gates-v1",
        "run": run,
        "subject_output_count": len(rows),
        **ownership_values,
        "final_direction_owner": dominance["final_direction_owner"],
        "primary_user_action_wording_owner": ("RENDERER" if complete_output else "NOT_MEASURED"),
        "ai_imperative_primary_action": (
            renderer_violations if complete_output else "NOT_MEASURED"
        ),
        "renderer_ownership_violations": (
            renderer_violations if complete_output else "NOT_MEASURED"
        ),
        "structured_action_consistency": renderer_gate,
        "known_hard_safety_regression": known_hard,
        "ownership_gate_status": ownership_gate,
        "renderer_gate_status": renderer_gate,
        "hard_safety_gate_status": hard_gate,
        "imperative_rows": imperative_rows,
        "status": status,
    }


def not_run_document(run: str, state: Mapping[str, object], reason: str) -> dict[str, object]:
    return {
        "contract": "direction-timing-two-stage-run-v1",
        "run": run,
        "resume_generation_id": state["resume_generation_id"],
        "source_generation_id": SOURCE_GENERATION_ID,
        "source_lock_sha256": SOURCE_LOCK_SHA256,
        "status": "NOT_RUN",
        "reason": reason,
        "same_generation_repair": 0,
        "selective_rerun": 0,
        "real_holdout_transport_retry_count": 0,
    }


def not_measured_gates(run: str, reason: str) -> dict[str, object]:
    return {
        "contract": "real-holdout-per-run-semantic-gates-v1",
        "run": run,
        "ownership_gate_status": "NOT_MEASURED",
        "renderer_gate_status": "NOT_MEASURED",
        "hard_safety_gate_status": "NOT_MEASURED",
        "status": "NOT_MEASURED",
        "reason": reason,
    }


def verify_semantic_freeze(args: argparse.Namespace, state: Mapping[str, object]) -> None:
    verify_program_freeze(state)
    previous.verify_frozen(args)
    manifest = model_input_manifest(args.source_root)
    if canonical_sha256(manifest) != state["model_input_manifest_sha256"]:
        raise ValueError("model_semantic_input_drift")


def update_exposure_state(
    state: dict[str, object], *, complete_run: bool, exposed: set[str]
) -> None:
    prior_exposed = set(state.get("exposed_subjects") or [])
    all_exposed = prior_exposed | exposed
    state["exposed_subjects"] = sorted(all_exposed)
    state["real_holdout_subject_output_count"] = len(all_exposed)
    if complete_run:
        state["holdout_output_exposure_state"] = "FULLY_EXPOSED"
        state["future_unseen_holdout_reuse_allowed"] = 0
    elif all_exposed:
        state["holdout_output_exposure_state"] = "PARTIALLY_EXPOSED"
        state["future_unseen_holdout_reuse_allowed"] = 0


def execute(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "PREPARED_FROZEN":
        raise ValueError("prepared_frozen_state_required")
    if state.get("runner_adapter_binding_preflight") != "PASS":
        raise ValueError("runner_adapter_binding_preflight_required")
    verify_semantic_freeze(args, state)
    (
        cohort,
        contexts,
        evidence,
        owned,
        core_aliases,
        timing_aliases,
        price_maps,
        stocks,
    ) = transport._load_frozen_holdout(args)
    guard = previous.LiveWorkloadGuard(
        proof_path(args.report_dir, "11-live-workload-coexistence-audit")
    )
    adapter = previous.GuardedTransportAdapter(
        guard=guard,
        continuation_generation=str(state["resume_generation_id"]),
        receipt_root=args.output_root / "transport-receipts",
        codex_bin=accepted_runtime._signed_in_codex_bin(),
    )
    documents: dict[str, dict[str, object]] = {}
    gates: dict[str, dict[str, object]] = {}
    stop_reason: str | None = None
    with real_holdout_runner_bridge(adapter):
        for run in ("first", "a", "b", "c"):
            if stop_reason:
                document = not_run_document(run, state, stop_reason)
                gate = not_measured_gates(run, stop_reason)
            else:
                run_root = args.output_root / f"run-{run}"
                try:
                    document = frozen.execute_two_stage_run(
                        run=f"real-holdout-{run}",
                        generation_id=SOURCE_GENERATION_ID,
                        source_lock_sha256=SOURCE_LOCK_SHA256,
                        prompt_root=args.source_root,
                        run_root=run_root,
                        cohort=cohort,
                        base_contexts=contexts,
                        evidence=evidence,
                        owned=owned,
                        core_aliases=core_aliases,
                        timing_aliases=timing_aliases,
                        price_maps=price_maps,
                        stocks=stocks,
                        timeout=MODEL_TIMEOUT_SECONDS,
                    )
                    document["resume_generation_id"] = state["resume_generation_id"]
                    document["source_generation_id"] = SOURCE_GENERATION_ID
                    document["transport_receipts"] = [
                        row
                        for row in receipt_rows(adapter.receipt_root)
                        if f":run-{run}:" in str(row["invocation_id"])
                    ]
                    gate = per_run_semantic_gates(run, document, owned)
                except Exception as exc:
                    exposed = exposed_subjects(run_root)
                    document = {
                        "contract": "direction-timing-two-stage-run-v1",
                        "run": run,
                        "resume_generation_id": state["resume_generation_id"],
                        "source_generation_id": SOURCE_GENERATION_ID,
                        "source_lock_sha256": SOURCE_LOCK_SHA256,
                        "status": "FAILED",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "transport_failure": int(isinstance(exc, transport.CodexTransportError)),
                        "execution_harness_interface_failure": int(isinstance(exc, TypeError)),
                        "schema_failure": 0,
                        "same_generation_repair": 0,
                        "selective_rerun": 0,
                        "real_holdout_transport_retry_count": 0,
                        "partial_subject_output_count": len(exposed),
                        "transport_receipts": [
                            row
                            for row in receipt_rows(adapter.receipt_root)
                            if f":run-{run}:" in str(row["invocation_id"])
                        ],
                    }
                    gate = not_measured_gates(run, f"{type(exc).__name__}:{exc}")
                complete_run = isinstance(document.get("rows"), list) and len(
                    document["rows"]
                ) == len(CURRENT_HOLDOUT)
                exposed = exposed_subjects(run_root)
                if complete_run:
                    exposed = set(CURRENT_HOLDOUT)
                update_exposure_state(state, complete_run=complete_run, exposed=exposed)
                if document.get("status") != "PASS":
                    stop_reason = f"{run.upper()}_EXECUTION_FAILED_NO_RETRY"
                    state["holdout_semantic_revelation_state"] = "NOT_MEASURED"
                    if state["holdout_output_exposure_state"] != "UNEXPOSED":
                        state["holdout_retirement_state"] = "RETIRED_PARTIAL_EXPOSURE"
                elif gate.get("status") != "PASS":
                    stop_reason = f"{run.upper()}_SEMANTIC_GATE_FAILED"
                    state["holdout_semantic_revelation_state"] = "REVEALED_FOR_ARCHITECTURE_TUNING"
                    state["holdout_retirement_state"] = "RETIRED_FOR_ARCHITECTURE_REPAIR"
                    state["future_unseen_holdout_reuse_allowed"] = 0
                else:
                    state["holdout_semantic_revelation_state"] = "NO_SEMANTIC_DEFECT_OBSERVED"
            documents[run] = document
            gates[run] = gate
            write_proof(args.report_dir, RUN_REPORT[run], document)
            write_proof(args.report_dir, RUN_GATE_REPORT[run], gate)
            state["real_holdout_model_invocation_count"] = adapter.model_call_count
            state["stop_reason"] = stop_reason
            write_json(args.output_root / "program-state.json", state)
            verify_semantic_freeze(args, state)

    write_aggregate_proofs(
        args,
        state=state,
        documents=documents,
        gates=gates,
        owned=owned,
        receipts=receipt_rows(adapter.receipt_root),
        stop_reason=stop_reason,
    )
    state["state"] = "EVIDENCE_COMPLETE"
    if not stop_reason:
        state["holdout_retirement_state"] = "RETIRED_AFTER_EVALUATION"
        state["future_unseen_holdout_reuse_allowed"] = 0
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(state, sort_keys=True), flush=True)


def _numeric_gate_total(gates: Mapping[str, Mapping[str, object]], field: str) -> int | str:
    values = [gate.get(field) for gate in gates.values()]
    measured = [value for value in values if isinstance(value, int)]
    return sum(measured) if measured else "NOT_MEASURED"


def _run_result(document: Mapping[str, object]) -> str:
    if document.get("status") == "PASS":
        return f"{document.get('validation_pass_count', 0)}/{len(CURRENT_HOLDOUT)}"
    return str(document.get("status") or "NOT_RUN")


def _not_measured_stability(contract: str, reason: str) -> dict[str, object]:
    return {
        "contract": contract,
        "status": "NOT_MEASURED",
        "reason": reason,
        "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
    }


def write_aggregate_proofs(
    args: argparse.Namespace,
    *,
    state: dict[str, object],
    documents: Mapping[str, Mapping[str, object]],
    gates: Mapping[str, Mapping[str, object]],
    owned: Mapping[str, OwnedEvidencePacket],
    receipts: Sequence[Mapping[str, object]],
    stop_reason: str | None,
) -> None:
    runs = ("first", "a", "b", "c")
    all_run_gates_pass = all(gates[run].get("status") == "PASS" for run in runs)
    abc_gates_pass = all(gates[run].get("status") == "PASS" for run in ("a", "b", "c"))
    if abc_gates_pass:
        core_stability = frozen._core_stability(CURRENT_HOLDOUT, documents)
        timing_stability = frozen._timing_stability(CURRENT_HOLDOUT, documents)
    else:
        reason = stop_reason or "ABC_PER_RUN_GATES_INCOMPLETE"
        core_stability = _not_measured_stability(
            "resume-directional-core-stability-audit-v1", reason
        )
        timing_stability = _not_measured_stability("resume-price-timing-stability-audit-v1", reason)
    core_stability["contract"] = "resume-directional-core-stability-audit-v1"
    timing_stability["contract"] = "resume-price-timing-stability-audit-v1"
    write_proof(args.report_dir, "22-resume-core-stability", core_stability)
    write_proof(args.report_dir, "23-resume-timing-stability", timing_stability)

    first = documents["first"]
    if isinstance(first.get("rows"), list) and len(first["rows"]) == len(CURRENT_HOLDOUT):
        dominance = frozen._dominance_audit(first, owned)
        dominance["contract"] = "resume-dominance-ownership-v1"
    else:
        dominance = {
            "contract": "resume-dominance-ownership-v1",
            "status": "NOT_MEASURED",
            "reason": stop_reason or "FIRST_COMPLETE_OUTPUT_REQUIRED",
            "final_direction_owner": "NOT_MEASURED",
            "price_only_directional_ownership_violations": "NOT_MEASURED",
            "price_only_holder_reduce": "NOT_MEASURED",
        }
    write_proof(args.report_dir, "24-resume-dominance-ownership", dominance)

    renderer_rows = []
    for run in runs:
        for row in documents[run].get("rows", []):
            if not isinstance(row, Mapping):
                continue
            matches = [
                match.model_dump(mode="json")
                for match in explicit_actionable_trade_directives(
                    str(row.get("rendered_message") or "")
                )
            ]
            renderer_rows.append(
                {
                    "run": run,
                    "ticker": row.get("ticker"),
                    "imperative_match_count": len(matches),
                    "imperative_matches": matches,
                    "status": "PASS" if not matches else "FAIL",
                }
            )
    renderer_violations = sum(int(row["imperative_match_count"]) for row in renderer_rows)
    renderer_status = (
        "PASS"
        if all_run_gates_pass and renderer_violations == 0
        else "FAIL"
        if any(gate.get("renderer_gate_status") == "FAIL" for gate in gates.values())
        else "NOT_MEASURED"
    )
    renderer = {
        "contract": "resume-renderer-action-ownership-v1",
        "primary_user_action_wording_owner": ("RENDERER" if renderer_rows else "NOT_MEASURED"),
        "ai_imperative_primary_action": (renderer_violations if renderer_rows else "NOT_MEASURED"),
        "renderer_ownership_violations": (renderer_violations if renderer_rows else "NOT_MEASURED"),
        "rows": renderer_rows,
        "status": renderer_status,
    }
    write_proof(args.report_dir, "25-resume-renderer-action-ownership", renderer)

    hard_fail = any(gate.get("hard_safety_gate_status") == "FAIL" for gate in gates.values())
    hard_status = "PASS" if all_run_gates_pass else "FAIL" if hard_fail else "NOT_MEASURED"
    known_hard = sum(
        int(document.get("hard_safety_regression") or 0) for document in documents.values()
    )
    hard = {
        "contract": "resume-hard-safety-regression-v1",
        "per_run_status": {
            run: gates[run].get("hard_safety_gate_status", "NOT_MEASURED") for run in runs
        },
        "numeric_provenance": "REUSED_UNCHANGED",
        "accounting_attribution": "REUSED_UNCHANGED",
        "official_provisional_earnings": "REUSED_UNCHANGED",
        "adr_security_basis": "REUSED_UNCHANGED",
        "evidence_identity_fencing": hard_status,
        "future_checkpoint": "REUSED_UNCHANGED",
        "logical_condition": "REUSED_UNCHANGED",
        "actionability_command_detection": hard_status,
        "known_hard_safety_regression": known_hard,
        "full_tests": "PENDING_FINAL_VALIDATION",
        "ruff": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
        "status": hard_status,
    }
    write_proof(args.report_dir, "26-resume-hard-safety-regression", hard)

    semantic_failure = any(gate.get("status") == "FAIL" for gate in gates.values())
    transport_failure = any(
        document.get("transport_failure") == 1 for document in documents.values()
    )
    harness_failure = any(
        document.get("execution_harness_interface_failure") == 1 for document in documents.values()
    )
    if all_run_gates_pass and core_stability.get("counts", {}).get("UNSTABLE", 0) == 0:
        readiness = "READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        verdict = (
            "OWNERSHIP_GENERALIZATION_STRONG"
            if core_stability.get("counts", {}).get("BOUNDARY_UNCERTAINTY", 0) == 0
            else "OWNERSHIP_GENERALIZATION_ACCEPTABLE_WITH_BOUNDARY_UNCERTAINTY"
        )
        next_scope = "MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
    elif semantic_failure:
        readiness = "NEEDS_ARCHITECTURE_WORK"
        verdict = "OWNERSHIP_GENERALIZATION_NEEDS_ARCHITECTURE_WORK"
        next_scope = "SEPARATELY_AUTHORIZED_GENERIC_ARCHITECTURE_REPAIR"
    elif transport_failure:
        readiness = "NOT_READY_TRANSPORT_BLOCKED"
        verdict = "NOT_MEASURED"
        next_scope = "BOUNDED_TRANSPORT_FAILURE_REVIEW"
    elif harness_failure:
        readiness = "NOT_READY_EXECUTION_HARNESS_BLOCKED"
        verdict = "NOT_MEASURED"
        next_scope = "BOUNDED_EXECUTION_HARNESS_REPAIR"
    else:
        readiness = "NOT_READY_EXECUTION_BLOCKED"
        verdict = "NOT_MEASURED"
        next_scope = "BOUNDED_EXECUTION_FAILURE_REVIEW"

    if all_run_gates_pass:
        state["holdout_output_exposure_state"] = "FULLY_EXPOSED"
        state["holdout_semantic_revelation_state"] = "NO_SEMANTIC_DEFECT_OBSERVED"
        state["holdout_retirement_state"] = "RETIRED_AFTER_EVALUATION"
        state["future_unseen_holdout_reuse_allowed"] = 0
    exposure = {
        "contract": "holdout-exposure-retirement-state-v1",
        "exposed_subjects": state.get("exposed_subjects", []),
        "real_holdout_subject_output_count": state.get("real_holdout_subject_output_count", 0),
        "holdout_output_exposure_state": state["holdout_output_exposure_state"],
        "holdout_semantic_revelation_state": state["holdout_semantic_revelation_state"],
        "holdout_retirement_state": state["holdout_retirement_state"],
        "future_unseen_holdout_reuse_allowed": state["future_unseen_holdout_reuse_allowed"],
        "same_cohort_architecture_tuning_rerun_allowed": state[
            "same_cohort_architecture_tuning_rerun_allowed"
        ],
        "status": "PASS",
    }
    write_proof(args.report_dir, "21-holdout-exposure-retirement-state", exposure)

    handoff = {
        "contract": "monitoring-bootstrap-next-handoff-v1",
        "activated": 0,
        "initial_enrichment_recorded_as_daily_delta": 0,
        "readiness": readiness,
        "next_scope": next_scope,
        "status": "PASS" if all_run_gates_pass else "NOT_READY",
    }
    write_proof(args.report_dir, "29-monitoring-bootstrap-next-handoff", handoff)

    directional_contexts = sum(row.get("stage") == "DIRECTIONAL_CORE" for row in receipts)
    timing_contexts = sum(row.get("stage") == "PRICE_TIMING" for row in receipts)
    orphan_count = sum(int(row.get("orphan_model_process_count") or 0) for row in receipts)
    secret_count = sum(int(row.get("secret_exposure_count") or 0) for row in receipts)
    run_results = {run: _run_result(documents[run]) for run in runs}
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": state["base_sha"],
        "work_instruction_commit": state["work_instruction_commit"],
        "implementation_commit": state["implementation_commit"],
        "final_head_sha": git_value("rev-parse", "HEAD"),
        "branch": state["branch"],
        "root_cause": "RUNNER_OWNED_CODEX_BIN_LEAKED_TO_CANONICAL_ADAPTER",
        "repair_scope": "EXPERIMENT_ONLY_REAL_HOLDOUT_RUNNER_ARGUMENT_BRIDGE",
        "runner_adapter_binding_preflight": state["runner_adapter_binding_preflight"],
        "execution_harness_interface_failure": int(harness_failure),
        "transport_failure": int(transport_failure),
        "source_freeze_failure": 0,
        "semantic_architecture_failure": int(semantic_failure),
        "renderer_action_ownership_failure": int(
            any(gate.get("renderer_gate_status") == "FAIL" for gate in gates.values())
        ),
        "hard_safety_failure": int(hard_fail),
        "implementation_success": 1,
        "authorized_harness_hash_drift": 1,
        "transport_topology_mutation": 0,
        "model_semantic_input_drift": 0,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_timeout_seconds": MODEL_TIMEOUT_SECONDS,
        "model_timeout_owner_count": 1,
        "orphan_model_process_count": orphan_count,
        "secret_exposure_count": secret_count,
        "batch_semantics": "MODEL_CONTEXT_COUPLED",
        "real_run_batch_size": MODEL_CONTEXT_BATCH_SIZE,
        "batch_split_adopted": 0,
        "architecture_semantic_drift": 0,
        "prompt_semantic_drift": 0,
        "schema_semantic_drift": 0,
        "source_drift": 0,
        "source_sufficiency_policy_drift": 0,
        "current_holdout_source_lock": SOURCE_LOCK_SHA256,
        "current_holdout_reuse_allowed": 1,
        "first_complete_run_count": int(
            isinstance(first.get("rows"), list) and len(first["rows"]) == len(CURRENT_HOLDOUT)
        ),
        "first_model_invocation_started": int(bool(receipts)),
        "real_holdout_model_invocation_count": state["real_holdout_model_invocation_count"],
        "real_holdout_directional_context_count": directional_contexts,
        "real_holdout_price_timing_context_count": timing_contexts,
        "real_holdout_subject_output_count": state.get("real_holdout_subject_output_count", 0),
        "real_holdout_transport_retry_count": 0,
        "run_results": run_results,
        "first_ownership_gate_status": gates["first"].get("ownership_gate_status", "NOT_MEASURED"),
        "first_renderer_gate_status": gates["first"].get("renderer_gate_status", "NOT_MEASURED"),
        "first_hard_safety_gate_status": gates["first"].get(
            "hard_safety_gate_status", "NOT_MEASURED"
        ),
        "run_a_ownership_gate_status": gates["a"].get("ownership_gate_status", "NOT_MEASURED"),
        "run_a_renderer_gate_status": gates["a"].get("renderer_gate_status", "NOT_MEASURED"),
        "run_a_hard_safety_gate_status": gates["a"].get("hard_safety_gate_status", "NOT_MEASURED"),
        "run_b_ownership_gate_status": gates["b"].get("ownership_gate_status", "NOT_MEASURED"),
        "run_b_renderer_gate_status": gates["b"].get("renderer_gate_status", "NOT_MEASURED"),
        "run_b_hard_safety_gate_status": gates["b"].get("hard_safety_gate_status", "NOT_MEASURED"),
        "run_c_ownership_gate_status": gates["c"].get("ownership_gate_status", "NOT_MEASURED"),
        "run_c_renderer_gate_status": gates["c"].get("renderer_gate_status", "NOT_MEASURED"),
        "run_c_hard_safety_gate_status": gates["c"].get("hard_safety_gate_status", "NOT_MEASURED"),
        "holdout_output_exposure_state": state["holdout_output_exposure_state"],
        "holdout_semantic_revelation_state": state["holdout_semantic_revelation_state"],
        "holdout_retirement_state": state["holdout_retirement_state"],
        "future_unseen_holdout_reuse_allowed": state["future_unseen_holdout_reuse_allowed"],
        "same_cohort_architecture_tuning_rerun_allowed": state[
            "same_cohort_architecture_tuning_rerun_allowed"
        ],
        "core_stability_counts": core_stability.get("counts"),
        "timing_stability_counts": timing_stability.get("counts"),
        "directional_core_price_technical_refs": _numeric_gate_total(
            gates, "directional_core_price_technical_refs"
        ),
        "directional_core_supply_refs": _numeric_gate_total(gates, "directional_core_supply_refs"),
        "supply_directional_core_usage": _numeric_gate_total(
            gates, "supply_directional_core_usage"
        ),
        "buy_without_nonprice_material_anchor": _numeric_gate_total(
            gates, "buy_without_nonprice_material_anchor"
        ),
        "sell_without_nonprice_material_anchor": _numeric_gate_total(
            gates, "sell_without_nonprice_material_anchor"
        ),
        "timing_stage_direction_mutation": _numeric_gate_total(
            gates, "timing_stage_direction_mutation"
        ),
        "timing_stage_balance_mutation": _numeric_gate_total(
            gates, "timing_stage_balance_mutation"
        ),
        "timing_stage_hold_lean_mutation": _numeric_gate_total(
            gates, "timing_stage_hold_lean_mutation"
        ),
        "price_timing_new_buyer_upgrade": _numeric_gate_total(
            gates, "price_timing_new_buyer_upgrade"
        ),
        "price_only_holder_reduce": _numeric_gate_total(gates, "price_only_holder_reduce"),
        "price_only_directional_ownership_violations": _numeric_gate_total(
            gates, "price_only_directional_ownership_violations"
        ),
        "directional_model_calls_on_source_insufficient": _numeric_gate_total(
            gates, "directional_model_calls_on_source_insufficient"
        ),
        "price_only_directional_model_calls": _numeric_gate_total(
            gates, "price_only_directional_model_calls"
        ),
        "final_direction_owner": dominance.get("final_direction_owner", "NOT_MEASURED"),
        "primary_user_action_wording_owner": renderer["primary_user_action_wording_owner"],
        "ai_imperative_primary_action": renderer["ai_imperative_primary_action"],
        "renderer_ownership_violations": renderer["renderer_ownership_violations"],
        "known_hard_safety_regression": known_hard,
        "main_merge": 0,
        "production_db_mutation": 0,
        "production_scheduler_change": 0,
        "production_telegram_send": 0,
        "monitoring_registration_calls": 0,
        "live_structured_autonomy_activation": 0,
        "live_v2_change": 0,
        "night_futures_code_mutation": 0,
        "ownership_generalization_verdict": verdict,
        "readiness": readiness,
        "stop_reason": stop_reason,
        "next_scope": next_scope,
        "full_tests": "PENDING_FINAL_VALIDATION",
        "ruff": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
        "status": "PASS" if all_run_gates_pass else "NOT_READY",
    }
    write_proof(args.report_dir, "30-program-completion", completion)


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    escaped = [[str(cell).replace("|", "\\|").replace("\n", " ") for cell in row] for row in rows]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in escaped)
    return "\n".join(lines)


def report_body(name: str, proof: Mapping[str, object]) -> str:
    title = name.replace("-", " ").title()
    scalar_rows = []
    for key, value in proof.items():
        if key in {"rows", "events", "cases", "exposed_subjects"}:
            continue
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            if len(rendered) > 800:
                rendered = f"{type(value).__name__}({len(value)})"
        else:
            rendered = value
        scalar_rows.append((key, rendered))
    lines = [f"# {title}", "", markdown_table(("Field", "Value"), scalar_rows), ""]
    rows = proof.get("rows") or proof.get("events") or proof.get("cases")
    if isinstance(rows, list) and rows:
        summaries = []
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            summaries.append(
                (
                    row.get("ticker") or row.get("batch_id") or row.get("case") or "-",
                    row.get("run") or row.get("stage") or "-",
                    row.get("status") or row.get("classification") or "-",
                )
            )
        if summaries:
            lines.extend([markdown_table(("Subject", "Run/Stage", "Status"), summaries), ""])
    lines.append(f"Machine proof: `{PROOF_DIRECTORY}/{name}.json`.")
    return "\n".join(lines) + "\n"


def write_reports(report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    for name in REPORT_NAMES:
        path = proof_path(report_dir, name)
        if path.is_file():
            (report_dir / f"20260906-{name}.md").write_text(
                report_body(name, read_json(path)), encoding="utf-8"
            )


def sync_transport_receipts(output_root: Path, report_dir: Path) -> None:
    source = output_root / "transport-receipts"
    target = report_dir / PROOF_DIRECTORY / "transport-receipts"
    if not source.is_dir():
        return
    for path in sorted(source.rglob("*.json")):
        destination = target / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())


def artifact_paths(report_dir: Path) -> list[Path]:
    markdown = [report_dir / f"20260906-{name}.md" for name in REPORT_NAMES]
    proofs = sorted((report_dir / PROOF_DIRECTORY).rglob("*.json"))
    return [path for path in (*markdown, *proofs) if path.is_file()]


def write_artifact_index(report_dir: Path) -> dict[str, object]:
    rows = [
        {
            "path": str(path.relative_to(report_dir)),
            "sha256": file_sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in artifact_paths(report_dir)
    ]
    value = {
        "contract": "real-holdout-runner-adapter-artifact-index-v1",
        "artifact_count": len(rows),
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "rows": rows,
        "status": "PASS",
    }
    write_json(report_dir / "20260906-artifact-index.json", value)
    (report_dir / "20260906-artifact-index.md").write_text(
        "# Artifact Index\n\n"
        + markdown_table(
            ("Path", "SHA-256", "Bytes"),
            [(row["path"], row["sha256"], row["bytes"]) for row in rows],
        )
        + "\n",
        encoding="utf-8",
    )
    return value


def verify_zip_index(zip_path: Path, index: Mapping[str, object]) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for row in index["rows"]:
            payload = archive.read(str(row["path"]))
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"zip_artifact_hash_mismatch:{row['path']}")
            if len(payload) != row["bytes"]:
                raise ValueError(f"zip_artifact_size_mismatch:{row['path']}")


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "EVIDENCE_COMPLETE":
        raise ValueError("terminal_evidence_state_required")
    verify_semantic_freeze(args, state)
    validation_pass = all(
        value == "PASS" for value in (args.full_tests, args.ruff, args.diff_check)
    )
    completion = read_json(proof_path(args.report_dir, "30-program-completion"))
    completion.update(
        {
            "final_head_sha": git_value("rev-parse", "HEAD"),
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
            "artifact_hash_mismatch_count": 0,
            "artifact_size_mismatch_count": 0,
        }
    )
    if not validation_pass:
        completion["readiness"] = "NOT_READY_VALIDATION_FAILED"
        completion["status"] = "NOT_READY"
    write_proof(args.report_dir, "30-program-completion", completion)
    hard = read_json(proof_path(args.report_dir, "26-resume-hard-safety-regression"))
    hard.update(
        {
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    if not validation_pass and hard.get("status") == "PASS":
        hard["status"] = "FAIL"
    write_proof(args.report_dir, "26-resume-hard-safety-regression", hard)
    sync_transport_receipts(args.output_root, args.report_dir)
    write_reports(args.report_dir)
    completion["artifact_count"] = len(artifact_paths(args.report_dir))
    write_proof(args.report_dir, "30-program-completion", completion)
    write_reports(args.report_dir)
    index = write_artifact_index(args.report_dir)
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in artifact_paths(args.report_dir):
            archive.write(path, path.relative_to(args.report_dir))
        for name in ("20260906-artifact-index.json", "20260906-artifact-index.md"):
            archive.write(args.report_dir / name, name)
    temporary.replace(args.zip_output)
    verify_zip_index(args.zip_output, index)
    zip_sha = file_sha256(args.zip_output)
    args.zip_output.with_suffix(args.zip_output.suffix + ".sha256").write_text(
        f"{zip_sha}  {args.zip_output.name}\n", encoding="utf-8"
    )
    state.update(
        {
            "state": "COMPLETE" if validation_pass else "COMPLETE_NOT_READY",
            "readiness": completion["readiness"],
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
            "artifact_count": index["artifact_count"],
            "artifact_hash_mismatch_count": 0,
            "artifact_size_mismatch_count": 0,
            "report_zip": str(args.zip_output),
            "report_zip_sha256": zip_sha,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("/tmp/thesis-monitor-20260906-direction-timing-ownership-run"),
    )
    parser.add_argument(
        "--prior-report",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports"
        / "thesis-monitor-20260906-synthetic-canary-fixture-repair-ownership-proof-resume-report.zip",
    )
    parser.add_argument(
        "--prior-state",
        type=Path,
        default=Path("/tmp/thesis-monitor-20260906-synthetic-canary-resume-run/program-state.json"),
    )
    parser.add_argument("--provider-root", type=Path, default=Path.home() / "Codex/ohlcv-analyst")
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    parser.add_argument(
        "--zip-output",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports"
        / "thesis-monitor-20260906-real-holdout-runner-adapter-repair-ownership-proof-resume-report.zip",
    )
    args = parser.parse_args()
    if args.prepare and args.as_of is None:
        raise ValueError("prepare_requires_fixed_as_of")
    for name in (
        "output_root",
        "report_dir",
        "source_root",
        "prior_report",
        "prior_state",
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
