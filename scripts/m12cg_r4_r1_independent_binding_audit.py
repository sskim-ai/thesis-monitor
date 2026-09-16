from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2FundamentalCoreBatch,
    AcceptedV2ProductionContext,
    load_accepted_v2_production_artifact,
    materialize_accepted_v2_stage2_output,
    parse_accepted_v2_production_artifact,
    validate_accepted_v2_fundamental_core,
    validate_accepted_v2_fundamental_core_batch_scope,
    validate_accepted_v2_production_output,
)
from app.services.decision_canary_service import canonical_sha256


CORE_SOURCE_HASHES = {
    1: "dba70bde34bb2791ed45408fcacfa7f8207fd816d9c9a518cea9aedaddc859ec",
    2: "134f87dbda8c5b857a70ac237d3b80a2593be09f5d9a625303e656bd2630d309",
    3: "2d33dce25eb87cddefe1f95bcc74757043ceb51aee4727a6fe907c52b6ca896f",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _delivery_consumer_probe(
    *,
    output_root: Path,
    artifact,
    trusted_batch: AcceptedV2FundamentalCoreBatch,
) -> dict[str, object]:
    from app.services import ai_assisted_delivery_service as delivery

    packet = {
        "packet_id": artifact.packet_id,
        "market": artifact.market,
        "assessment_date": artifact.assessment_date,
        "stocks": [{"ticker": ticker} for ticker in artifact.selected_subjects],
    }
    delivery_artifact = artifact.model_copy(
        update={"source_packet_sha256": canonical_sha256(packet)}
    )
    output_path = output_root / "native-consumer" / "review.json"
    paths = delivery.accepted_v2_production_paths(
        output_path,
        claim_id=artifact.claim_id,
    )
    _write_json(paths["final"], delivery_artifact.model_dump(mode="json"))
    _write_json(paths["core_temp"], trusted_batch.model_dump(mode="json"))
    settings = delivery.get_settings().model_copy(
        update={
            "visible_stock_decision_engine": "v2_accepted",
            "v2_production_enabled": True,
            "v2_full_monitored_stock_coverage_target": True,
            "v1_decision_rollback_available": True,
        }
    )
    original_get_settings = delivery.get_settings
    delivery.get_settings = lambda: settings
    try:
        loaded, state, loaded_path = delivery._load_delivery_accepted_v2(
            packet,
            SimpleNamespace(claim_id=artifact.claim_id),
            output_path,
        )
    finally:
        delivery.get_settings = original_get_settings
    compositions: list[dict[str, object]] = []
    if loaded is not None:
        blocks = {row.ticker: row for row in loaded.blocks}
        for ticker in ("GOOGL", "HUT"):
            block = blocks[ticker]
            base_text = f"{ticker} deterministic base message"
            combined = delivery.insert_decision_canary_block(base_text, block.text)
            compositions.append(
                {
                    "ticker": ticker,
                    "accepted_block_id": block.accepted_decision_id,
                    "block_exactly_in_composed_message": block.text in combined,
                    "base_message_preserved": base_text in combined,
                    "within_existing_message_limit": (
                        len(combined) <= settings.telegram_message_max_chars
                    ),
                    "composed_text": combined,
                }
            )
    status = (
        "PASS"
        if loaded is not None
        and state == "PASS"
        and loaded_path == paths["final"]
        and loaded.selected_subjects == artifact.selected_subjects
        and len(compositions) == 2
        and all(
            row["block_exactly_in_composed_message"]
            and row["base_message_preserved"]
            and row["within_existing_message_limit"]
            for row in compositions
        )
        else "FAIL"
    )
    result = {
        "contract": "m12cg-r4-r1-native-consumer-v1",
        "consumer": (
            "_load_delivery_accepted_v2 + insert_decision_canary_block"
        ),
        "artifact_path": paths["final"].relative_to(output_root).as_posix(),
        "trusted_core_path": paths["core_temp"].relative_to(output_root).as_posix(),
        "artifact_state": state,
        "base_ai_fallback_used": False,
        "notifier_invoked": False,
        "production_send": 0,
        "compositions": compositions,
        "status": status,
    }
    _write_json(output_root / "native-consumer-proof.json", result)
    return result


def run_audit(*, m12ce_root: Path, r4_root: Path, output_root: Path) -> dict[str, object]:
    raw_root = m12ce_root / "raw" / "reproof-no-repair" / "us"
    r4_payload_root = r4_root / "payloads" / "fresh"
    binding_rows: list[dict[str, object]] = []
    parity_rows: list[dict[str, object]] = []
    subject_rows: list[dict[str, object]] = []
    native_consumer_result: dict[str, object] | None = None

    for batch_number in range(1, 4):
        label = f"batch-{batch_number:02d}"
        core_path = raw_root / f"core-batch-{batch_number:02d}.output.json"
        context_path = r4_payload_root / f"{label}.context.json"
        stage2_path = r4_payload_root / f"{label}.source-output.json"
        expected_artifact_path = r4_payload_root / f"{label}.artifact.json"

        core_source_sha = _sha256(core_path)
        context = AcceptedV2ProductionContext.model_validate_json(
            context_path.read_text(encoding="utf-8")
        )
        trusted_batch = AcceptedV2FundamentalCoreBatch.model_validate_json(
            core_path.read_text(encoding="utf-8")
        )
        scope_errors = validate_accepted_v2_fundamental_core_batch_scope(
            trusted_batch,
            context,
            subjects=context.selected_subjects,
        )
        ownership = {row.ticker: row for row in context.evidence_ownership}
        semantic_errors = {
            core.ticker: list(
                validate_accepted_v2_fundamental_core(core, ownership[core.ticker])
            )
            for core in trusted_batch.cores
        }
        raw_stage2 = _json(stage2_path)
        if not isinstance(raw_stage2, dict):
            raise ValueError(f"stage2_payload_invalid:{label}")
        output = materialize_accepted_v2_stage2_output(context, raw_stage2)
        core_matches_materialized = tuple(output.fundamental_cores) == tuple(
            trusted_batch.cores
        )
        expected_artifact = parse_accepted_v2_production_artifact(
            _json(expected_artifact_path)
        )
        artifact = validate_accepted_v2_production_output(
            context,
            output,
            trusted_fundamental_core_batch=trusted_batch,
            validated_at=datetime.fromisoformat(expected_artifact.validated_at),
        )
        artifact_byte_parity = (
            canonical_sha256(artifact.model_dump(mode="json"))
            == canonical_sha256(expected_artifact.model_dump(mode="json"))
        )

        packet = {
            "packet_id": artifact.packet_id,
            "market": artifact.market,
            "assessment_date": artifact.assessment_date,
            "stocks": [{"ticker": ticker} for ticker in artifact.selected_subjects],
        }
        reader_artifact = artifact.model_copy(
            update={"source_packet_sha256": canonical_sha256(packet)}
        )
        reader_path = output_root / "payloads" / f"{label}.reader-artifact.json"
        _write_json(reader_path, reader_artifact.model_dump(mode="json"))
        loaded = load_accepted_v2_production_artifact(
            reader_path,
            packet=packet,
            claim_id=artifact.claim_id,
            trusted_fundamental_core_batch=trusted_batch,
        )
        reader_round_trip = canonical_sha256(
            loaded.model_dump(mode="json")
        ) == canonical_sha256(reader_artifact.model_dump(mode="json"))
        if batch_number == 2:
            native_consumer_result = _delivery_consumer_probe(
                output_root=output_root,
                artifact=artifact,
                trusted_batch=trusted_batch,
            )

        core_copy = output_root / "independent-core-sources" / core_path.name
        core_copy.parent.mkdir(parents=True, exist_ok=True)
        core_copy.write_bytes(core_path.read_bytes())
        batch_pass = bool(
            core_source_sha == CORE_SOURCE_HASHES[batch_number]
            and not scope_errors
            and not any(semantic_errors.values())
            and core_matches_materialized
            and artifact_byte_parity
            and reader_round_trip
            and artifact.ready_count == len(context.selected_subjects)
            and artifact.not_ready_count == 0
        )
        binding_rows.append(
            {
                "batch": batch_number,
                "source_path": core_path.as_posix(),
                "copied_source_path": core_copy.relative_to(output_root).as_posix(),
                "expected_whole_file_sha256": CORE_SOURCE_HASHES[batch_number],
                "observed_whole_file_sha256": core_source_sha,
                "source_is_separate_from_tested_stage2_output": core_path != stage2_path,
                "scope_errors": list(scope_errors),
                "semantic_errors": semantic_errors,
                "subjects": list(context.selected_subjects),
                "status": "PASS" if batch_pass else "FAIL",
            }
        )
        parity_rows.append(
            {
                "batch": batch_number,
                "subjects": list(context.selected_subjects),
                "core_matches_materialized_stage2": core_matches_materialized,
                "artifact_byte_parity": artifact_byte_parity,
                "reader_round_trip_with_independent_core": reader_round_trip,
                "ready_count": artifact.ready_count,
                "not_ready_count": artifact.not_ready_count,
                "status": "PASS" if batch_pass else "FAIL",
            }
        )
        expected_plans = {
            plan.ticker: plan for plan in expected_artifact.accepted_plans
        }
        expected_blocks = {block.ticker: block for block in expected_artifact.blocks}
        for plan, block in zip(artifact.accepted_plans, artifact.blocks, strict=True):
            subject_pass = bool(
                plan == expected_plans[plan.ticker]
                and block == expected_blocks[block.ticker]
                and plan.status == "READY"
            )
            subject_rows.append(
                {
                    "ticker": plan.ticker,
                    "batch": batch_number,
                    "accepted_plan_parity": plan == expected_plans[plan.ticker],
                    "renderer_parity": block == expected_blocks[block.ticker],
                    "accepted_decision": plan.accepted_decision,
                    "status": "PASS" if subject_pass else "FAIL",
                }
            )

    binding_result = {
        "contract": "m12cg-r4-r1-independent-core-source-binding-v1",
        "original_core_validation_owner": (
            "validate_accepted_v2_fundamental_core_batch_scope + "
            "validate_accepted_v2_fundamental_core"
        ),
        "independent_core_source_count": len(binding_rows),
        "core_reference_derived_from_tested_output": False,
        "batches": binding_rows,
        "status": (
            "PASS" if all(row["status"] == "PASS" for row in binding_rows) else "FAIL"
        ),
    }
    parity_result = {
        "contract": "m12cg-r4-r1-fresh-parity-v1",
        "batch_count": len(parity_rows),
        "subject_count": len(subject_rows),
        "ready_count": sum(row["status"] == "PASS" for row in subject_rows),
        "batches": parity_rows,
        "subjects": subject_rows,
        "status": (
            "PASS"
            if len(parity_rows) == 3
            and len(subject_rows) == 9
            and all(row["status"] == "PASS" for row in parity_rows)
            and all(row["status"] == "PASS" for row in subject_rows)
            else "FAIL"
        ),
    }
    _write_json(output_root / "independent-core-source-binding.json", binding_result)
    _write_json(output_root / "fresh-9-subject-3-batch-parity.json", parity_result)
    result = {
        "contract": "m12cg-r4-r1-independent-binding-audit-v1",
        "independent_binding": binding_result["status"],
        "fresh_parity": parity_result["status"],
        "native_consumer": (
            native_consumer_result["status"]
            if native_consumer_result is not None
            else "NOT_RUN"
        ),
        "status": (
            "PASS"
            if binding_result["status"] == "PASS"
            and parity_result["status"] == "PASS"
            and native_consumer_result is not None
            and native_consumer_result["status"] == "PASS"
            else "FAIL"
        ),
    }
    _write_json(output_root / "audit-result.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m12ce-root", type=Path, required=True)
    parser.add_argument("--r4-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    result = run_audit(
        m12ce_root=args.m12ce_root.resolve(),
        r4_root=args.r4_root.resolve(),
        output_root=args.output_root.resolve(),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
