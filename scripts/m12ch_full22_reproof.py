from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import subprocess
import traceback
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

from app.jobs import accepted_decision_v2_runtime as runtime
from app.services import ai_assisted_delivery_service as delivery
from app.services.accepted_decision_v2_runtime_service import (
    REASONING_EFFORT,
    REASONING_MODEL,
    STAGE2_MATURITY_AS_OF_AGGREGATION,
    STAGE2_MATURITY_AS_OF_SEMANTICS,
    STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT,
    STAGE2_MODEL_OUTPUT_CONTRACT,
    AcceptedV2FundamentalCoreBatch,
    AcceptedV2ProductionArtifactV2,
    AcceptedV2ProductionBatchOutputV2,
    AcceptedV2ProductionContext,
    accepted_v2_fundamental_core_from_candidate,
    accepted_v2_fundamental_core_sha256,
    accepted_v2_maturity_atomic_claim_catalog,
    accepted_v2_stage2_validation_scope_manifest,
    load_accepted_v2_production_artifact,
    validate_accepted_v2_fundamental_core,
    validate_accepted_v2_fundamental_core_batch_scope,
    validate_accepted_v2_maturity_atomic_identity,
    validate_accepted_v2_production_output,
)
from app.services.evidence_maturity_pricing_service import (
    concrete_evidence_date,
    project_maturity_provenance,
)
from app.services.preconfirmation_decision_v2_service import (
    _EXACT_NUMBER,
    _UNSUPPORTED,
    requires_preconfirmation_buy,
    stage2_owned_candidate_claims,
)
from scripts import v2_production_cutover_preflight as preflight


REPO = Path(__file__).resolve().parents[1]
REQUIRED_BASE = "1e0d81695ce0982827a35a58b5123dfb86e066cc"
INSTRUCTION_COMMIT_PREFIX = "fa0b645c"
EXPECTED = {
    "us": {
        "file_sha256": ("2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228"),
        "canonical_sha256": ("78f9c31b351e36e1811e77b286b480c9bd85eed1157234861fe7f6855dbc194a"),
        "claim_id": "preflight-us-20260902",
        "subjects": (
            "CORZ",
            "CPNG",
            "CRCL",
            "GOOGL",
            "HUT",
            "IBM",
            "MU",
            "RXRX",
            "SKHY",
            "SNDK",
            "TSLA",
            "TSM",
            "WRD",
            "WULF",
        ),
    },
    "kr": {
        "file_sha256": ("819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597"),
        "canonical_sha256": ("b18bf36d4b03091079d5c607edf0f6f23076223ae333ef2f27eaec9437549663"),
        "claim_id": "preflight-kr-20260902",
        "subjects": (
            "000660",
            "003690",
            "005490",
            "005930",
            "010120",
            "012450",
            "047810",
            "086280",
        ),
    },
}


class ReproofFailure(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ReproofFailure(code)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReproofFailure(f"expected_json_object:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def git(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def ref_occurrences(value: object, path: str = "$") -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in {
                "evidence_refs",
                "supporting_evidence_refs",
                "contradicting_evidence_refs",
                "supporting_claim_refs",
                "contradicting_claim_refs",
            } and isinstance(child, list):
                found.extend(
                    {"path": f"{child_path}[{index}]", "kind": key, "ref": str(ref)}
                    for index, ref in enumerate(child)
                )
            elif key in {"source_condition_ref", "leaf_ref"} and isinstance(child, str):
                found.append({"path": child_path, "kind": key, "ref": child})
            found.extend(ref_occurrences(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(ref_occurrences(child, f"{path}[{index}]"))
    return found


def exact_ref_errors(output: Path, catalog: Path) -> list[dict[str, str]]:
    payload = read_json(output)
    manifest = read_json(catalog)
    evidence = {str(value) for value in manifest["allowed_refs"]}
    maturity_claims = {str(value) for value in manifest.get("allowed_maturity_claim_refs") or []}
    sources = {str(value) for value in manifest["allowed_source_condition_refs"]}
    leaves = {str(value) for value in manifest["allowed_leaf_refs"]}
    errors: list[dict[str, str]] = []
    for row in ref_occurrences(payload):
        allowed = (
            sources
            if row["kind"] == "source_condition_ref"
            else leaves
            if row["kind"] == "leaf_ref"
            else maturity_claims
            if row["kind"] in {"supporting_claim_refs", "contradicting_claim_refs"}
            else evidence
        )
        if row["ref"] not in allowed:
            errors.append(row)
    return errors


def stage2_raw_contract_audit(output: Path) -> dict[str, object]:
    payload = read_json(output)
    rows: list[dict[str, object]] = []
    authored_as_of = 0
    authored_provenance = 0
    for candidate_index, candidate in enumerate(payload.get("candidates") or []):
        if not isinstance(candidate, dict):
            continue
        for row_index, maturity in enumerate(candidate.get("driver_maturity") or []):
            if not isinstance(maturity, dict):
                continue
            has_as_of = "as_of" in maturity
            has_provenance = "provenance_status" in maturity
            authored_as_of += int(has_as_of)
            authored_provenance += int(has_provenance)
            rows.append(
                {
                    "path": (f"$.candidates[{candidate_index}].driver_maturity[{row_index}]"),
                    "ticker": str(candidate.get("ticker") or ""),
                    "model_authored_as_of": has_as_of,
                    "model_authored_provenance_status": has_provenance,
                }
            )
    return {
        "contract": payload.get("contract"),
        "contract_valid": payload.get("contract") == STAGE2_MODEL_OUTPUT_CONTRACT,
        "candidate_count": len(payload.get("candidates") or []),
        "maturity_row_count": len(rows),
        "model_authored_as_of_count": authored_as_of,
        "model_authored_provenance_status_count": authored_provenance,
        "rows": rows,
        "status": (
            "PASS"
            if payload.get("contract") == STAGE2_MODEL_OUTPUT_CONTRACT
            and authored_as_of == 0
            and authored_provenance == 0
            else "FAIL"
        ),
    }


def call_key(output: Path) -> tuple[str, str, int]:
    market = output.parent.name
    stem = output.name.removesuffix(".output.json")
    if stem.startswith("core-batch-"):
        return market, "FUNDAMENTAL_CORE", int(stem.rsplit("-", 1)[-1])
    if stem.startswith("batch-") and ".repair" not in stem:
        return market, "PRICE_TIMING", int(stem.rsplit("-", 1)[-1])
    raise ReproofFailure(f"forbidden_or_unknown_model_call:{output.name}")


def build_call_plan(
    contexts: list[AcceptedV2ProductionContext],
    model_manifest: dict[str, Any],
) -> list[dict[str, object]]:
    frozen = {(str(row["market"]), int(row["batch"])): row for row in model_manifest["batches"]}
    rows: list[dict[str, object]] = []
    ordinal = 0
    for context in contexts:
        for stage in ("FUNDAMENTAL_CORE", "PRICE_TIMING"):
            for index in range(0, len(context.selected_subjects), runtime.V2_REASONING_BATCH_SIZE):
                ordinal += 1
                batch = index // runtime.V2_REASONING_BATCH_SIZE + 1
                subjects = list(
                    context.selected_subjects[index : index + runtime.V2_REASONING_BATCH_SIZE]
                )
                source = frozen[(context.market, batch)]
                rows.append(
                    {
                        "ordinal": ordinal,
                        "market": context.market,
                        "stage": stage,
                        "batch": batch,
                        "subjects": subjects,
                        "expected_subject_count": len(subjects),
                        "schema_semantic_sha256": (
                            source["fundamental_core_schema_semantic_sha256"]
                            if stage == "FUNDAMENTAL_CORE"
                            else None
                        ),
                        "ref_catalog_hash": (
                            source["fundamental_core_ref_catalog_hash"]
                            if stage == "FUNDAMENTAL_CORE"
                            else None
                        ),
                        "ref_catalog_count": (
                            source["fundamental_core_ref_catalog_count"]
                            if stage == "FUNDAMENTAL_CORE"
                            else None
                        ),
                        "ticker_domain_hash": source["ticker_domain_hash"],
                        "identity_contract_hash": source["identity_contract_hash"],
                        "exact_prompt_sha256": (
                            source["fundamental_core_prompt_sha256"]
                            if stage == "FUNDAMENTAL_CORE"
                            else None
                        ),
                        "freeze_state": (
                            "FROZEN_BEFORE_CALL_1"
                            if stage == "FUNDAMENTAL_CORE"
                            else "ASSIGNMENT_FROZEN_BEFORE_CALL_1;"
                            "EXACT_STAGE2_PAYLOAD_FROZEN_AFTER_NEW_CORE"
                        ),
                        "status": "PLANNED",
                    }
                )
    require(len(rows) == 16, "planned_model_call_count_drift")
    return rows


def trusted_batch_from_freezes(
    *,
    context: AcceptedV2ProductionContext,
    market_dir: Path,
) -> AcceptedV2FundamentalCoreBatch:
    cores = []
    mapping: list[dict[str, object]] = []
    for index in range(0, len(context.selected_subjects), runtime.V2_REASONING_BATCH_SIZE):
        batch_number = index // runtime.V2_REASONING_BATCH_SIZE + 1
        path = market_dir / "core-stage-freeze" / f"core-batch-{batch_number:02d}.json"
        batch = AcceptedV2FundamentalCoreBatch.model_validate(read_json(path))
        subjects = context.selected_subjects[index : index + runtime.V2_REASONING_BATCH_SIZE]
        errors = validate_accepted_v2_fundamental_core_batch_scope(
            batch, context, subjects=subjects
        )
        require(not errors, f"trusted_core_scope_invalid:{context.market}:{batch_number}")
        cores.extend(batch.cores)
        mapping.append(
            {
                "batch": batch_number,
                "subjects": list(subjects),
                "source_path": str(path),
                "source_sha256": file_sha256(path),
            }
        )
    trusted = AcceptedV2FundamentalCoreBatch(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        cores=tuple(cores),
    )
    errors = validate_accepted_v2_fundamental_core_batch_scope(
        trusted, context, subjects=context.selected_subjects
    )
    require(not errors, f"trusted_market_core_scope_invalid:{context.market}")
    ownership = {row.ticker: row for row in context.evidence_ownership}
    semantic_errors = {
        core.ticker: list(validate_accepted_v2_fundamental_core(core, ownership[core.ticker]))
        for core in trusted.cores
    }
    require(
        not any(semantic_errors.values()),
        f"trusted_market_core_semantic_invalid:{context.market}",
    )
    write_json(
        market_dir / "independent-core-stage-binding.json",
        {
            "contract": "m12ch-independent-core-stage-binding-v1",
            "market": context.market,
            "subject_count": len(trusted.cores),
            "source_is_separate_from_stage2_output": True,
            "core_reference_derived_from_tested_output": False,
            "batches": mapping,
            "semantic_errors": semantic_errors,
            "status": "PASS",
        },
    )
    return trusted


def native_delivery_readback(
    *,
    output_root: Path,
    packet: dict[str, Any],
    artifact: AcceptedV2ProductionArtifactV2,
    trusted_core: AcceptedV2FundamentalCoreBatch,
) -> dict[str, object]:
    marker = output_root / "native-consumer" / "review.json"
    paths = delivery.accepted_v2_production_paths(marker, claim_id=artifact.claim_id)
    write_json(paths["final"], artifact.model_dump(mode="json"))
    write_json(paths["core_temp"], trusted_core.model_dump(mode="json"))
    settings = delivery.get_settings().model_copy(
        update={
            "visible_stock_decision_engine": "v2_accepted",
            "v2_production_enabled": True,
            "v2_full_monitored_stock_coverage_target": True,
            "v1_decision_rollback_available": True,
        }
    )
    original = delivery.get_settings
    delivery.get_settings = lambda: settings
    try:
        loaded, state, loaded_path = delivery._load_delivery_accepted_v2(
            packet,
            SimpleNamespace(claim_id=artifact.claim_id),
            marker,
        )
    finally:
        delivery.get_settings = original
    require(loaded is not None, f"native_delivery_readback_missing:{artifact.market}")
    require(state == "PASS", f"native_delivery_readback_state:{artifact.market}:{state}")
    require(loaded_path == paths["final"], f"native_delivery_path_mismatch:{artifact.market}")
    require(
        canonical_sha256(loaded.model_dump(mode="json"))
        == canonical_sha256(artifact.model_dump(mode="json")),
        f"native_delivery_artifact_mismatch:{artifact.market}",
    )
    result = {
        "contract": "m12ch-native-delivery-readback-v1",
        "market": artifact.market,
        "artifact_path": str(paths["final"]),
        "trusted_core_path": str(paths["core_temp"]),
        "subject_count": len(loaded.selected_subjects),
        "artifact_state": state,
        "production_send": 0,
        "notifier_invoked": False,
        "status": "PASS",
    }
    write_json(output_root / "native-delivery-readback.json", result)
    return result


async def run(args: argparse.Namespace) -> None:
    package_root = args.package_root.resolve()
    premodel_root = args.premodel_root.resolve()
    premodel = read_json(premodel_root / "premodel-audit.json")
    require(premodel.get("status") == "PASS", "premodel_gate_failed")
    head = git("rev-parse", "HEAD")
    require(head == args.expected_head, "harness_head_drift")
    require(head == premodel["harness_freeze_commit"], "premodel_head_mismatch")
    require(not git("status", "--porcelain"), "worktree_not_clean")
    require(
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", REQUIRED_BASE, head),
            cwd=REPO,
            check=False,
        ).returncode
        == 0,
        "required_base_not_ancestor",
    )
    require(
        git("rev-parse", INSTRUCTION_COMMIT_PREFIX) == premodel["instruction_commit"],
        "instruction_commit_drift",
    )
    require(REASONING_MODEL == "gpt-5.6-sol", "model_contract_drift")
    require(REASONING_EFFORT == "xhigh", "reasoning_effort_contract_drift")

    packets = {
        market: package_root / f"inputs/frozen-packets/{market}.json" for market in ("us", "kr")
    }
    deterministic = {
        market: premodel_root / f"deterministic/{market}-deterministic.json"
        for market in ("us", "kr")
    }
    contexts: list[AcceptedV2ProductionContext] = []
    packet_payloads: dict[str, dict[str, Any]] = {}
    for market in ("us", "kr"):
        expected = EXPECTED[market]
        require(
            file_sha256(packets[market]) == expected["file_sha256"],
            f"{market}:packet_sha_drift",
        )
        context = await preflight._context(packets[market], claim_id=str(expected["claim_id"]))
        require(
            context.source_packet_sha256 == expected["canonical_sha256"],
            f"{market}:canonical_packet_sha_drift",
        )
        require(
            tuple(context.selected_subjects) == expected["subjects"],
            f"{market}:subject_order_drift",
        )
        contexts.append(context)
        packet_payloads[market] = read_json(packets[market])

    now_utc = datetime.now(UTC)
    now_kst = now_utc.astimezone(ZoneInfo("Asia/Seoul"))
    generation_id = f"{now_kst:%Y%m%d}-uskr22-m12ch-{now_utc:%Y%m%dT%H%M%SZ}-{head[:12]}"
    output_root = args.output_parent.resolve() / generation_id
    require(not output_root.exists(), "generation_output_already_exists")
    output_root.mkdir(parents=True)

    model_manifest = read_json(premodel_root / "fundamental-core-freeze-manifest.json")
    require(model_manifest.get("status") == "PASS", "model_manifest_not_frozen")
    call_plan = build_call_plan(contexts, model_manifest)
    plan_by_key = {
        (str(row["market"]), str(row["stage"]), int(row["batch"])): row for row in call_plan
    }
    summary: dict[str, Any] = {
        "contract": "m12ch-frozen-contract-full22-reproof-v1",
        "generation_id": generation_id,
        "assessment_date": "2026-09-15",
        "fresh_generation_not_current_market_collection": True,
        "required_runtime_base": REQUIRED_BASE,
        "instruction_commit": premodel["instruction_commit"],
        "harness_freeze_commit": head,
        "runtime_tree_sha256": premodel["runtime_tree_sha256"],
        "reasoning_model": REASONING_MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "raw_stage2_contract": STAGE2_MODEL_OUTPUT_CONTRACT,
        "normalization_contract": STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT,
        "maturity_as_of_semantics": STAGE2_MATURITY_AS_OF_SEMANTICS,
        "maturity_as_of_aggregation": STAGE2_MATURITY_AS_OF_AGGREGATION,
        "status": "RUNNING",
        "top_level_result": "RUNNING",
        "planned_model_call_count": 16,
        "model_calls_started": 0,
        "model_calls_completed": 0,
        "model_calls_with_usable_output": 0,
        "fundamental_core_accepted_count": 0,
        "stage2_raw_contract_accepted_count": 0,
        "stage2_materialized_candidate_count": 0,
        "stage2_semantic_accepted_count": 0,
        "accepted_plan_finalized_count": 0,
        "rendered_block_count": 0,
        "composed_message_count": 0,
        "native_readback_count": 0,
        "raw_model_authored_as_of_count": 0,
        "raw_model_authored_provenance_status_count": 0,
        "exact_ref_violation_count": 0,
        "maturity_provenance_violation_count": 0,
        "maturity_atomic_identity_failure_count": 0,
        "stage2_owned_exact_numeric_violation_count": 0,
        "stage2_owned_unsupported_metric_failure_count": 0,
        "preconfirmation_contract_failure_count": 0,
        "independent_core_reference_count": 0,
        "wrapper_retry_count": 0,
        "fallback_model_call_count": 0,
        "judge_call_count": 0,
        "repair_call_count": 0,
        "schema_repair_call_count": 0,
        "candidate_repair_call_count": 0,
        "selective_rerun_count": 0,
        "per_ticker_retry_count": 0,
        "hotfix_count": 0,
        "prior_output_reuse_count": 0,
        "cross_generation_stitch_count": 0,
        "production_db_mutations": 0,
        "assessment_production_writes": 0,
        "warning_production_mutations": 0,
        "notification_production_queue_writes": 0,
        "production_sends": 0,
        "scheduler_mutation_count": 0,
        "main_merges": 0,
        "deployments": 0,
        "remote_push_count": 0,
        "model_calls": call_plan,
        "markets": {},
        "started_at_utc": now_utc.isoformat(),
        "started_at_kst": now_kst.isoformat(),
    }
    write_json(
        output_root / "input-freeze.json",
        {
            "generation_id": generation_id,
            "assessment_date": "2026-09-15",
            "runtime_tree_sha256": premodel["runtime_tree_sha256"],
            "premodel_audit_sha256": file_sha256(premodel_root / "premodel-audit.json"),
            "model_manifest_sha256": file_sha256(
                premodel_root / "fundamental-core-freeze-manifest.json"
            ),
            "markets": {
                context.market: {
                    "packet_id": context.packet_id,
                    "claim_id": context.claim_id,
                    "whole_file_sha256": file_sha256(packets[context.market]),
                    "canonical_source_packet_sha256": context.source_packet_sha256,
                    "subjects": list(context.selected_subjects),
                    "deterministic_snapshot_sha256": file_sha256(deterministic[context.market]),
                }
                for context in contexts
            },
            "frozen_at": datetime.now(UTC).isoformat(),
        },
    )
    write_json(
        output_root / "full-call-plan-pre-call1.json",
        {
            "generation_id": generation_id,
            "planned_model_call_count": 16,
            "no_repair": True,
            "calls": call_plan,
            "frozen_at": datetime.now(UTC).isoformat(),
        },
    )
    write_json(output_root / "run-freeze.json", summary)

    original_invoke = preflight._invoke_signed_in_codex
    original_output_class = preflight.AcceptedV2ProductionBatchOutput
    runtime.V2_TRANSPORT_ATTEMPT_LIMIT = 1
    preflight.V2_BATCH_SCHEMA_REPAIR_LIMIT = 0
    preflight.AcceptedV2ProductionBatchOutput = AcceptedV2ProductionBatchOutputV2

    def forbidden_repair(*args: object, **kwargs: object) -> str:
        del args, kwargs
        raise ReproofFailure("repair_path_forbidden_by_m12ch")

    preflight.accepted_v2_production_repair_prompt = forbidden_repair
    preflight.accepted_v2_production_batch_schema_repair_prompt = forbidden_repair

    def tracked_invoke(**kwargs: Any) -> dict[str, object]:
        output = Path(kwargs["output"])
        prompt = Path(kwargs["prompt"])
        schema = Path(kwargs["schema"])
        market, stage, batch = call_key(output)
        row = plan_by_key[(market, stage, batch)]
        require(row["status"] == "PLANNED", "duplicate_model_call_detected")
        catalog = output.parent / (output.name.removesuffix(".output.json") + ".ref-catalog.json")
        require(catalog.exists(), f"missing_ref_catalog:{market}:{stage}:{batch}")
        schema_payload = read_json(schema)
        catalog_payload = read_json(catalog)
        actual_schema_hash = canonical_sha256(schema_payload)
        actual_prompt_hash = file_sha256(prompt)
        if stage == "FUNDAMENTAL_CORE":
            require(
                actual_schema_hash == row["schema_semantic_sha256"],
                f"core_schema_hash_drift:{market}:{batch}",
            )
            require(
                actual_prompt_hash == row["exact_prompt_sha256"],
                f"core_prompt_hash_drift:{market}:{batch}",
            )
            require(
                catalog_payload["ref_catalog_hash"] == row["ref_catalog_hash"],
                f"core_ref_catalog_hash_drift:{market}:{batch}",
            )
            require(
                catalog_payload["ref_catalog_count"] == row["ref_catalog_count"],
                f"core_ref_catalog_count_drift:{market}:{batch}",
            )
        else:
            maturity = schema_payload["$defs"]["DriverEvidenceMaturity"]
            require("as_of" not in maturity["properties"], "model_schema_as_of_exposed")
            require(
                "provenance_status" not in maturity["properties"],
                "model_schema_provenance_status_exposed",
            )
            require(maturity.get("additionalProperties") is False, "model_schema_not_strict")
            require(
                bool(catalog_payload.get("allowed_maturity_claim_refs")),
                f"stage2_atomic_claim_catalog_empty:{market}:{batch}",
            )
            row.update(
                {
                    "schema_semantic_sha256": actual_schema_hash,
                    "ref_catalog_hash": catalog_payload["ref_catalog_hash"],
                    "ref_catalog_count": catalog_payload["ref_catalog_count"],
                    "maturity_date_catalog_hash": catalog_payload["maturity_date_catalog_hash"],
                    "maturity_atomic_claim_catalog_hash": catalog_payload[
                        "maturity_atomic_claim_catalog_hash"
                    ],
                    "exact_prompt_sha256": actual_prompt_hash,
                    "freeze_state": "FROZEN_AFTER_NEW_CORE_BEFORE_STAGE2_MODEL_CALL",
                }
            )
        row.update(
            {
                "status": "STARTED",
                "actual_schema_file_sha256": file_sha256(schema),
                "actual_schema_size_bytes": schema.stat().st_size,
                "actual_prompt_size_bytes": prompt.stat().st_size,
                "started_at": datetime.now(UTC).isoformat(),
            }
        )
        summary["model_calls_started"] += 1
        write_json(output_root / "summary.json", summary)
        write_json(
            output_root / "full-call-plan-frozen-progress.json",
            {"generation_id": generation_id, "calls": call_plan},
        )
        print(
            f"START {row['ordinal']}/16 {market} {stage} "
            f"batch={batch} subjects={','.join(row['subjects'])}",
            flush=True,
        )
        receipt = original_invoke(**kwargs)
        attempts = int(receipt.get("transport_attempts") or 0)
        require(attempts == 1, "model_transport_retry_detected")
        summary["wrapper_retry_count"] += max(0, attempts - 1)
        summary["model_calls_completed"] += 1
        row.update(
            {
                "status": "MODEL_OUTPUT_CREATED",
                "transport": receipt,
                "output_sha256": file_sha256(output),
                "completed_at": datetime.now(UTC).isoformat(),
            }
        )
        raw_copy = (
            output.parent
            / "raw-response-freeze"
            / f"{output.name.removesuffix('.output.json')}.json"
        )
        raw_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output, raw_copy)
        require(file_sha256(raw_copy) == file_sha256(output), "raw_response_copy_mismatch")
        row["raw_response_freeze"] = str(raw_copy)

        if stage == "FUNDAMENTAL_CORE":
            batch_payload = AcceptedV2FundamentalCoreBatch.model_validate(read_json(output))
            expected_subjects = tuple(str(value) for value in row["subjects"])
            scope_errors = validate_accepted_v2_fundamental_core_batch_scope(
                batch_payload,
                next(context for context in contexts if context.market == market),
                subjects=expected_subjects,
            )
            require(not scope_errors, f"core_scope_invalid:{market}:{batch}")
            ownership = {
                item.ticker: item
                for context in contexts
                if context.market == market
                for item in context.evidence_ownership
            }
            semantic_errors = {
                core.ticker: list(
                    validate_accepted_v2_fundamental_core(core, ownership[core.ticker])
                )
                for core in batch_payload.cores
            }
            require(
                not any(semantic_errors.values()),
                f"core_semantic_invalid:{market}:{batch}",
            )
            freeze = output.parent / "core-stage-freeze" / f"core-batch-{batch:02d}.json"
            freeze.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output, freeze)
            require(file_sha256(freeze) == file_sha256(output), "core_freeze_copy_mismatch")
            row["independent_core_freeze_path"] = str(freeze)
            row["batch_identity_audit"] = {
                "expected_tickers": list(expected_subjects),
                "returned_tickers": [core.ticker for core in batch_payload.cores],
                "scope_errors": list(scope_errors),
                "semantic_errors": semantic_errors,
                "status": "PASS",
            }
            summary["fundamental_core_accepted_count"] += len(batch_payload.cores)
        else:
            raw_audit = stage2_raw_contract_audit(output)
            row["raw_contract_audit"] = raw_audit
            require(raw_audit["status"] == "PASS", f"stage2_raw_contract_failure:{market}:{batch}")
            summary["raw_model_authored_as_of_count"] += raw_audit["model_authored_as_of_count"]
            summary["raw_model_authored_provenance_status_count"] += raw_audit[
                "model_authored_provenance_status_count"
            ]
            summary["stage2_raw_contract_accepted_count"] += raw_audit["candidate_count"]

        ref_errors = exact_ref_errors(output, catalog)
        if ref_errors:
            row["exact_ref_violations"] = ref_errors
            summary["exact_ref_violation_count"] += len(ref_errors)
            write_json(output_root / "summary.json", summary)
            raise ReproofFailure(
                f"exact_ref_failure:{market}:{stage}:{batch}:{ref_errors[0]['ref']}"
            )
        row["status"] = "RAW_OUTPUT_PASS"
        summary["model_calls_with_usable_output"] += 1
        write_json(output_root / "summary.json", summary)
        print(f"COMPLETE {row['ordinal']}/16 {market} {stage} batch={batch}", flush=True)
        return receipt

    preflight._invoke_signed_in_codex = tracked_invoke

    try:
        artifacts: list[AcceptedV2ProductionArtifactV2] = []
        outputs: dict[str, AcceptedV2ProductionBatchOutputV2] = {}
        native_readbacks: list[dict[str, object]] = []
        trusted_by_market: dict[str, AcceptedV2FundamentalCoreBatch] = {}
        for context in contexts:
            market_dir = output_root / context.market
            market_dir.mkdir(parents=True)
            write_json(market_dir / "context.json", context.model_dump(mode="json"))
            generated = preflight._codex_batch(
                context,
                output_dir=market_dir,
                timeout=args.timeout,
                state_namespace=f"m12ch:{generation_id}:{context.market}",
            )
            require(
                isinstance(generated, AcceptedV2ProductionBatchOutputV2),
                f"{context.market}:normalized_output_not_v2",
            )
            trusted = trusted_batch_from_freezes(
                context=context,
                market_dir=market_dir,
            )
            require(
                tuple(generated.fundamental_cores) == tuple(trusted.cores),
                f"{context.market}:stage2_core_copy_mismatch",
            )
            trusted_path = market_dir / "trusted-fundamental-core-batch.json"
            write_json(trusted_path, trusted.model_dump(mode="json"))
            candidate_path = market_dir / "candidate-output.json"
            write_json(candidate_path, generated.model_dump(mode="json"))
            artifact = validate_accepted_v2_production_output(
                context,
                generated,
                trusted_fundamental_core_batch=trusted,
            )
            require(
                isinstance(artifact, AcceptedV2ProductionArtifactV2),
                f"{context.market}:artifact_not_v2",
            )
            artifact_path = market_dir / "accepted-artifact.json"
            write_json(artifact_path, artifact.model_dump(mode="json"))
            loaded = load_accepted_v2_production_artifact(
                artifact_path,
                packet=packet_payloads[context.market],
                claim_id=context.claim_id,
                trusted_fundamental_core_batch=trusted,
            )
            require(
                canonical_sha256(loaded.model_dump(mode="json"))
                == canonical_sha256(artifact.model_dump(mode="json")),
                f"{context.market}:service_reader_round_trip_mismatch",
            )
            require(
                artifact.status == "PASS"
                and artifact.ready_count == len(context.selected_subjects)
                and artifact.not_ready_count == 0,
                f"{context.market}:aggregate_not_fully_valid",
            )
            native = native_delivery_readback(
                output_root=market_dir,
                packet=packet_payloads[context.market],
                artifact=artifact,
                trusted_core=trusted,
            )
            native_readbacks.append(native)
            artifacts.append(artifact)
            outputs[context.market] = generated
            trusted_by_market[context.market] = trusted
            summary["markets"][context.market] = {
                "packet_id": context.packet_id,
                "source_packet_sha256": context.source_packet_sha256,
                "subject_count": len(context.selected_subjects),
                "subjects": list(context.selected_subjects),
                "ready_count": artifact.ready_count,
                "not_ready_count": artifact.not_ready_count,
                "status": artifact.status,
                "trusted_core_sha256": file_sha256(trusted_path),
                "candidate_output_sha256": file_sha256(candidate_path),
                "accepted_artifact_sha256": file_sha256(artifact_path),
                "service_reader_round_trip": "PASS",
                "native_delivery_readback": native["status"],
            }
            for row in call_plan:
                if row["market"] == context.market and row["status"] == "RAW_OUTPUT_PASS":
                    row["status"] = "PASS"
            write_json(output_root / "summary.json", summary)

        messages = preflight._production_payloads(
            artifacts,
            (deterministic["us"], deterministic["kr"]),
        )
        require(len(messages) == 22, "composed_message_count_drift")
        require(
            len({str(row["ticker"]) for row in messages}) == 22,
            "composed_message_subject_duplication",
        )
        write_json(output_root / "shadow-production-payloads.json", {"messages": messages})

        all_candidates = [
            candidate for output in outputs.values() for candidate in output.candidates
        ]
        all_cores = [core for batch in trusted_by_market.values() for core in batch.cores]
        all_blocks = [block for artifact in artifacts for block in artifact.blocks]
        core_by_ticker = {row.ticker: row for row in all_cores}
        block_by_ticker = {row.ticker: row for row in all_blocks}
        ticker_market = {
            ticker: context.market for context in contexts for ticker in context.selected_subjects
        }
        context_by_market = {context.market: context for context in contexts}

        provenance_rows: list[dict[str, object]] = []
        provenance_failures: list[dict[str, object]] = []
        for candidate in all_candidates:
            context = context_by_market[ticker_market[candidate.ticker]]
            packet = next(row for row in context.evidence_packets if row.ticker == candidate.ticker)
            ownership = next(
                row for row in context.evidence_ownership if row.ticker == candidate.ticker
            )
            visible_refs = {
                ref_id
                for ref_id in (*ownership.core_ref_ids, *ownership.timing_ref_ids)
                if not ref_id.startswith("technical-feature:")
            }
            evidence = {row.ref_id: row for row in packet.evidence if row.ref_id in visible_refs}
            assessment_date = date.fromisoformat(context.assessment_date)
            for index, maturity in enumerate(candidate.driver_maturity):
                refs = tuple(
                    dict.fromkeys(
                        (
                            *maturity.supporting_evidence_refs,
                            *maturity.contradicting_evidence_refs,
                        )
                    )
                )
                projection = project_maturity_provenance(evidence, refs)
                projected_status = (
                    projection.provenance_status.value
                    if projection.provenance_status is not None
                    else None
                )
                status_valid = maturity.provenance_status == projected_status
                as_of_valid = maturity.as_of == projection.as_of
                concrete = concrete_evidence_date(maturity.as_of)
                future_valid = concrete is None or concrete <= assessment_date
                valid = (
                    not projection.invalid_ref_ids
                    and projection.provenance_status is not None
                    and status_valid
                    and as_of_valid
                    and future_valid
                )
                row = {
                    "market": context.market,
                    "ticker": candidate.ticker,
                    "row_index": index,
                    "cited_refs": list(refs),
                    "concrete_dates": list(projection.concrete_dates),
                    "symbolic_ref_ids": list(projection.symbolic_ref_ids),
                    "invalid_ref_ids": list(projection.invalid_ref_ids),
                    "expected_as_of": projection.as_of,
                    "materialized_as_of": maturity.as_of,
                    "expected_provenance_status": projected_status,
                    "materialized_provenance_status": maturity.provenance_status,
                    "same_row_as_of_valid": as_of_valid,
                    "provenance_status_valid": status_valid,
                    "future_date_valid": future_valid,
                    "status": "PASS" if valid else "FAIL",
                }
                provenance_rows.append(row)
                if not valid:
                    provenance_failures.append(row)
        require(not provenance_failures, "maturity_provenance_projection_failure")

        maturity_rows: list[dict[str, object]] = []
        maturity_errors: list[dict[str, str]] = []
        for candidate in all_candidates:
            core = core_by_ticker[candidate.ticker]
            catalog = accepted_v2_maturity_atomic_claim_catalog(core)
            catalog_by_ref = {row.claim_ref: row for row in catalog}
            errors = validate_accepted_v2_maturity_atomic_identity(candidate, core)
            maturity_errors.extend({"ticker": candidate.ticker, "error": error} for error in errors)
            for index, maturity in enumerate(candidate.driver_maturity):
                supporting = [catalog_by_ref.get(ref) for ref in maturity.supporting_claim_refs]
                contradicting = [
                    catalog_by_ref.get(ref) for ref in maturity.contradicting_claim_refs
                ]
                maturity_rows.append(
                    {
                        "ticker": candidate.ticker,
                        "index": index,
                        "driver": maturity.driver,
                        "maturity": maturity.maturity,
                        "as_of": maturity.as_of,
                        "provenance_status": maturity.provenance_status,
                        "supporting_claim_refs": list(maturity.supporting_claim_refs),
                        "contradicting_claim_refs": list(maturity.contradicting_claim_refs),
                        "atomic_claim_overlap": sorted(
                            set(maturity.supporting_claim_refs)
                            & set(maturity.contradicting_claim_refs)
                        ),
                        "supporting_polarities": [
                            row.claim.polarity if row is not None else "UNKNOWN"
                            for row in supporting
                        ],
                        "contradicting_polarities": [
                            row.claim.polarity if row is not None else "UNKNOWN"
                            for row in contradicting
                        ],
                    }
                )
        require(not maturity_errors, "maturity_atomic_identity_failure")

        preconfirmation_rows = [
            {
                "ticker": candidate.ticker,
                "decision": candidate.decision,
                "required": requires_preconfirmation_buy(candidate),
                "pre_confirmation_buy": candidate.pre_confirmation_buy,
                "explanation_present": (candidate.preconfirmation_buy_explanation is not None),
                "new_buyer": candidate.new_buyer_axis.stance,
                "holder": candidate.holder_axis.stance,
            }
            for candidate in all_candidates
        ]
        preconfirmation_failures = [
            row
            for row in preconfirmation_rows
            if row["required"] != row["pre_confirmation_buy"]
            or row["pre_confirmation_buy"] != row["explanation_present"]
            or (row["pre_confirmation_buy"] and row["decision"] != "BUY")
        ]
        require(not preconfirmation_failures, "preconfirmation_contract_failure")

        stage2_numeric = {
            candidate.ticker: [
                claim.text
                for claim in stage2_owned_candidate_claims(candidate)
                if _EXACT_NUMBER.search(claim.text)
            ]
            for candidate in all_candidates
        }
        stage2_unsupported = {
            candidate.ticker: [
                claim.text
                for claim in stage2_owned_candidate_claims(candidate)
                if _UNSUPPORTED.search(claim.text)
            ]
            for candidate in all_candidates
        }
        require(not any(stage2_numeric.values()), "stage2_owned_exact_numeric_claim_failure")
        require(
            not any(stage2_unsupported.values()),
            "stage2_owned_unsupported_metric_failure",
        )

        per_ticker = []
        for candidate in all_candidates:
            core = core_by_ticker[candidate.ticker]
            block = block_by_ticker[candidate.ticker]
            core_hash_match = (
                candidate.fundamental_core_sha256 == accepted_v2_fundamental_core_sha256(core)
            )
            core_exact_copy = accepted_v2_fundamental_core_from_candidate(candidate) == core
            require(core_hash_match, f"core_hash_mutation:{candidate.ticker}")
            require(core_exact_copy, f"core_copy_mutation:{candidate.ticker}")
            per_ticker.append(
                {
                    "ticker": candidate.ticker,
                    "market": ticker_market[candidate.ticker],
                    "decision": candidate.decision,
                    "overall_maturity": candidate.overall_maturity.maturity,
                    "new_buyer": block.new_buyer_stance,
                    "holder": block.holder_stance,
                    "fundamental_core_hash_match": core_hash_match,
                    "fundamental_core_exact_copy": core_exact_copy,
                    "driver_maturity_count": len(candidate.driver_maturity),
                }
            )

        require(len(per_ticker) == 22, "per_ticker_count_drift")
        require(len(all_blocks) == 22, "rendered_block_count_drift")
        scope_manifest = accepted_v2_stage2_validation_scope_manifest()
        summary.update(
            {
                "status": "PASS",
                "top_level_result": "M12CH_FROZEN_CONTRACT_FULL22_REPROOF_PASS",
                "subject_count": 22,
                "fundamental_core_accepted_count": 22,
                "stage2_raw_contract_accepted_count": 22,
                "stage2_materialized_candidate_count": 22,
                "stage2_semantic_accepted_count": 22,
                "accepted_plan_finalized_count": 22,
                "rendered_block_count": len(all_blocks),
                "composed_message_count": len(messages),
                "native_readback_count": sum(int(row["subject_count"]) for row in native_readbacks),
                "independent_core_reference_count": len(all_cores),
                "maturity_row_count": len(provenance_rows),
                "symbolic_only_row_count": sum(
                    row["materialized_provenance_status"] == "SYMBOLIC_ONLY_NO_CONCRETE_DATE"
                    for row in provenance_rows
                ),
                "concrete_with_symbolic_row_count": sum(
                    row["materialized_provenance_status"] == "CONCRETE_WITH_SYMBOLIC_REFS"
                    for row in provenance_rows
                ),
                "concrete_only_row_count": sum(
                    row["materialized_provenance_status"] == "CONCRETE_ONLY"
                    for row in provenance_rows
                ),
                "maturity_provenance_violation_count": len(provenance_failures),
                "maturity_atomic_identity_failure_count": len(maturity_errors),
                "stage2_owned_exact_numeric_violation_count": sum(
                    len(rows) for rows in stage2_numeric.values()
                ),
                "stage2_owned_unsupported_metric_failure_count": sum(
                    len(rows) for rows in stage2_unsupported.values()
                ),
                "preconfirmation_contract_failure_count": len(preconfirmation_failures),
                "validation_scope_contract": scope_manifest["contract"],
                "provenance_rows": provenance_rows,
                "maturity_rows": maturity_rows,
                "preconfirmation_rows": preconfirmation_rows,
                "per_ticker_results": per_ticker,
                "message_model_contract_readiness": "FULL22_REPROVEN_LOCAL_ONLY",
                "deployment_readiness": "NO_BY_PHASE_BOUNDARY",
                "closed_designs_and_repairs": "CARRIED_FORWARD_AT_DOCUMENTED_SCOPE",
                "offline_acceptance": "PASS",
                "offline_operations": "PASS",
                "fresh_full22": "PASS",
                "deployment_authorization": "NOT_AUTHORIZED",
                "source_runtime_drift_count": 0,
                "model_facing_contract_drift_count": 0,
                "completed_at_utc": datetime.now(UTC).isoformat(),
                "completed_at_kst": datetime.now(UTC)
                .astimezone(ZoneInfo("Asia/Seoul"))
                .isoformat(),
            }
        )
        require(summary["model_calls_started"] == 16, "formal_call_start_count_drift")
        require(summary["model_calls_completed"] == 16, "formal_call_complete_count_drift")
        require(
            summary["model_calls_with_usable_output"] == 16,
            "formal_usable_call_count_drift",
        )
        require(not git("status", "--porcelain"), "worktree_changed_during_generation")
        write_json(output_root / "summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    except Exception as exc:
        for row in call_plan:
            if row["status"] == "PLANNED":
                row["status"] = "NOT_RUN_AFTER_FIRST_HARD_FAILURE"
        active = [row for row in call_plan if row["status"] != "NOT_RUN_AFTER_FIRST_HARD_FAILURE"]
        terminal = active[-1] if active else None
        summary.update(
            {
                "status": "FAIL",
                "top_level_result": "M12CH_FULL22_STOPPED_FIRST_HARD_FAILURE",
                "failure_type": type(exc).__name__,
                "failure": str(exc),
                "failure_ordinal": terminal["ordinal"] if terminal else None,
                "failure_market": terminal["market"] if terminal else None,
                "failure_stage": terminal["stage"] if terminal else None,
                "failure_batch": terminal["batch"] if terminal else None,
                "failure_subjects": terminal["subjects"] if terminal else [],
                "failure_raw_output_sha256": (terminal.get("output_sha256") if terminal else None),
                "message_model_contract_readiness": "NOT_READY",
                "deployment_readiness": "NO",
                "fresh_full22": "STOPPED_FIRST_HARD_FAILURE",
                "deployment_authorization": "NOT_AUTHORIZED",
                "completed_at_utc": datetime.now(UTC).isoformat(),
                "completed_at_kst": datetime.now(UTC)
                .astimezone(ZoneInfo("Asia/Seoul"))
                .isoformat(),
            }
        )
        write_json(output_root / "summary.json", summary)
        (output_root / "failure-traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
        raise
    finally:
        preflight._invoke_signed_in_codex = original_invoke
        preflight.AcceptedV2ProductionBatchOutput = original_output_class


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--premodel-root", type=Path, required=True)
    parser.add_argument("--output-parent", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
