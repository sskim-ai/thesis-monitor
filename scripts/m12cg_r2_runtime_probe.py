from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from app.services.accepted_decision_v2_runtime_service import (
    STAGE2_MODEL_OUTPUT_CONTRACT,
    AcceptedV2FundamentalCoreCandidate,
    AcceptedV2ProductionContext,
    accepted_v2_production_prompt,
    accepted_v2_stage2_output_schema,
    accepted_v2_stage2_ref_catalog_manifest,
    materialize_accepted_v2_stage2_output,
    validate_accepted_v2_production_output,
    validate_accepted_v2_stage2_candidate,
)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def pretty_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def subset_context(
    context: AcceptedV2ProductionContext,
    subjects: tuple[str, ...],
) -> AcceptedV2ProductionContext:
    selected = set(subjects)
    return context.model_copy(
        update={
            "selected_subjects": subjects,
            "evidence_packets": tuple(
                row for row in context.evidence_packets if row.ticker in selected
            ),
            "evidence_ownership": tuple(
                row for row in context.evidence_ownership if row.ticker in selected
            ),
            "prior_accepted": tuple(
                row for row in context.prior_accepted if row.ticker in selected
            ),
        }
    )


def subset_raw(raw: dict[str, object], subjects: tuple[str, ...]) -> dict[str, object]:
    selected = set(subjects)
    payload = deepcopy(raw)
    for field_name in ("fundamental_cores", "candidates", "adjudications"):
        rows = payload.get(field_name)
        if isinstance(rows, list):
            payload[field_name] = [
                row
                for row in rows
                if isinstance(row, dict) and str(row.get("ticker")) in selected
            ]
    return payload


def historical_raw(payload: dict[str, object]) -> dict[str, object]:
    raw = deepcopy(payload)
    raw["contract"] = STAGE2_MODEL_OUTPUT_CONTRACT
    candidates = raw.get("candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            rows = candidate.get("driver_maturity")
            if not isinstance(rows, list):
                continue
            for row in rows:
                if isinstance(row, dict):
                    row.pop("as_of", None)
                    row.pop("provenance_status", None)
    return raw


def write_payload(path: Path, payload: object) -> dict[str, object]:
    value = pretty_bytes(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)
    return {
        "path": path.name,
        "size": len(value),
        "pretty_sha256": sha256_bytes(value),
        "canonical_sha256": sha256_bytes(canonical_bytes(payload)),
    }


def probe_historical(
    source_root: Path,
    output_root: Path,
) -> dict[str, object]:
    batches: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    row_count = 0
    status_counts: Counter[str] = Counter()
    for market in ("us", "kr"):
        market_root = source_root / "raw" / "reproof-no-repair" / market
        context_path = market_root / "context.json"
        context = AcceptedV2ProductionContext.model_validate_json(
            context_path.read_text(encoding="utf-8")
        )
        packet_by_ticker = {row.ticker: row for row in context.evidence_packets}
        ownership_by_ticker = {
            row.ticker: row for row in context.evidence_ownership
        }
        for source_path in sorted(market_root.glob("batch-*.output.json")):
            source_bytes = source_path.read_bytes()
            original = json.loads(source_bytes)
            raw = historical_raw(original)
            subjects = tuple(str(row["ticker"]) for row in raw["candidates"])
            output = materialize_accepted_v2_stage2_output(
                context,
                raw,
                subjects=subjects,
            )
            payload = output.model_dump(mode="json")
            relative = source_path.relative_to(source_root).as_posix()
            saved = write_payload(
                output_root / "historical" / market / source_path.name,
                payload,
            )
            core_by_ticker = {row.ticker: row for row in output.fundamental_cores}
            for candidate in output.candidates:
                validation = validate_accepted_v2_stage2_candidate(
                    packet_by_ticker[candidate.ticker],
                    candidate,
                    core_by_ticker[candidate.ticker],
                    ownership_by_ticker[candidate.ticker],
                )
                candidate_payload = candidate.model_dump(mode="json")
                candidate_saved = write_payload(
                    output_root
                    / "historical"
                    / market
                    / f"{source_path.stem}--{candidate.ticker}.candidate.json",
                    candidate_payload,
                )
                candidate_rows = []
                for index, row in enumerate(candidate.driver_maturity):
                    status_counts[row.provenance_status.value] += 1
                    candidate_rows.append(
                        {
                            "row_index": index,
                            "driver": row.driver,
                            "as_of": row.as_of,
                            "provenance_status": row.provenance_status.value,
                            "canonical_sha256": sha256_bytes(
                                canonical_bytes(row.model_dump(mode="json"))
                            ),
                        }
                    )
                row_count += len(candidate_rows)
                candidates.append(
                    {
                        "market": market,
                        "source_output": relative,
                        "source_output_sha256": sha256_bytes(source_bytes),
                        "ticker": candidate.ticker,
                        "validation": "PASS" if validation.valid else "FAIL",
                        "validation_errors": list(validation.errors),
                        "payload": candidate_saved,
                        "rows": candidate_rows,
                    }
                )
            batches.append(
                {
                    "market": market,
                    "source_output": relative,
                    "source_output_sha256": sha256_bytes(source_bytes),
                    "subjects": list(subjects),
                    "candidate_count": len(output.candidates),
                    "row_count": sum(
                        len(candidate.driver_maturity)
                        for candidate in output.candidates
                    ),
                    "payload": saved,
                }
            )
    return {
        "batch_count": len(batches),
        "candidate_count": len(candidates),
        "row_count": row_count,
        "status_counts": dict(sorted(status_counts.items())),
        "valid_candidate_count": sum(
            row["validation"] == "PASS" for row in candidates
        ),
        "batches": batches,
        "candidates": candidates,
    }


def probe_fresh(source_root: Path, output_root: Path) -> dict[str, object]:
    raw_root = source_root / "raw" / "reproof-no-repair" / "us"
    context_path = raw_root / "context.json"
    context_bytes = context_path.read_bytes()
    context = AcceptedV2ProductionContext.model_validate_json(
        context_bytes.decode("utf-8")
    )
    batches: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    finalizations: list[dict[str, object]] = []
    model_facing: list[dict[str, object]] = []
    row_count = 0
    status_counts: Counter[str] = Counter()
    for batch_number in range(1, 4):
        source_path = raw_root / f"batch-{batch_number:02d}.output.json"
        source_bytes = source_path.read_bytes()
        raw = json.loads(source_bytes)
        subjects = tuple(str(row["ticker"]) for row in raw["candidates"])
        batch_context = subset_context(context, subjects)
        output = materialize_accepted_v2_stage2_output(batch_context, raw)
        payload = output.model_dump(mode="json")
        saved = write_payload(
            output_root / "fresh" / f"batch-{batch_number:02d}.normalized.json",
            payload,
        )
        cores = tuple(
            AcceptedV2FundamentalCoreCandidate.model_validate(row)
            for row in raw["fundamental_cores"]
        )
        prompt = accepted_v2_production_prompt(
            batch_context,
            fundamental_cores=cores,
            subjects=subjects,
        ).encode("utf-8")
        schema = pretty_bytes(
            accepted_v2_stage2_output_schema(
                batch_context,
                subjects=subjects,
                fundamental_cores=cores,
            )
        )
        catalog = pretty_bytes(
            accepted_v2_stage2_ref_catalog_manifest(
                batch_context,
                subjects=subjects,
                fundamental_cores=cores,
            )
        )
        model_facing.append(
            {
                "batch": batch_number,
                "subjects": list(subjects),
                "prompt_sha256": sha256_bytes(prompt),
                "schema_sha256": sha256_bytes(schema),
                "catalog_sha256": sha256_bytes(catalog),
            }
        )
        packet_by_ticker = {row.ticker: row for row in batch_context.evidence_packets}
        ownership_by_ticker = {
            row.ticker: row for row in batch_context.evidence_ownership
        }
        core_by_ticker = {row.ticker: row for row in output.fundamental_cores}
        for candidate in output.candidates:
            validation = validate_accepted_v2_stage2_candidate(
                packet_by_ticker[candidate.ticker],
                candidate,
                core_by_ticker[candidate.ticker],
                ownership_by_ticker[candidate.ticker],
            )
            candidate_payload = candidate.model_dump(mode="json")
            candidate_saved = write_payload(
                output_root / "fresh" / f"{candidate.ticker}.candidate.json",
                candidate_payload,
            )
            candidate_rows = []
            for index, row in enumerate(candidate.driver_maturity):
                status_counts[row.provenance_status.value] += 1
                candidate_rows.append(
                    {
                        "row_index": index,
                        "driver": row.driver,
                        "as_of": row.as_of,
                        "provenance_status": row.provenance_status.value,
                        "canonical_sha256": sha256_bytes(
                            canonical_bytes(row.model_dump(mode="json"))
                        ),
                    }
                )
            row_count += len(candidate_rows)
            candidates.append(
                {
                    "batch": batch_number,
                    "ticker": candidate.ticker,
                    "source_output_sha256": sha256_bytes(source_bytes),
                    "validation": "PASS" if validation.valid else "FAIL",
                    "validation_errors": list(validation.errors),
                    "payload": candidate_saved,
                    "rows": candidate_rows,
                }
            )

            one_context = subset_context(context, (candidate.ticker,))
            one_raw = subset_raw(raw, (candidate.ticker,))
            one_output = materialize_accepted_v2_stage2_output(one_context, one_raw)
            finalization: dict[str, object] = {
                "ticker": candidate.ticker,
                "batch": batch_number,
                "normalized_sha256": sha256_bytes(
                    canonical_bytes(one_output.model_dump(mode="json"))
                ),
            }
            try:
                artifact = validate_accepted_v2_production_output(
                    one_context,
                    one_output,
                    validated_at=datetime(2026, 9, 16, tzinfo=UTC),
                )
                artifact_payload = artifact.model_dump(mode="json")
                finalization.update(
                    {
                        "result": "PASS",
                        "artifact": write_payload(
                            output_root
                            / "fresh"
                            / f"{candidate.ticker}.artifact.json",
                            artifact_payload,
                        ),
                        "accepted_plan_sha256": sha256_bytes(
                            canonical_bytes(
                                artifact.accepted_plans[0].model_dump(mode="json")
                            )
                        ),
                        "renderer_text_sha256": sha256_bytes(
                            artifact.blocks[0].text.encode("utf-8")
                        )
                        if artifact.blocks
                        else None,
                    }
                )
            except Exception as exc:
                finalization.update(
                    {
                        "result": "FAIL",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
            finalizations.append(finalization)
        batches.append(
            {
                "batch": batch_number,
                "source_output_sha256": sha256_bytes(source_bytes),
                "subjects": list(subjects),
                "candidate_count": len(output.candidates),
                "row_count": sum(
                    len(candidate.driver_maturity)
                    for candidate in output.candidates
                ),
                "payload": saved,
            }
        )
    return {
        "context_sha256": sha256_bytes(context_bytes),
        "batch_count": len(batches),
        "candidate_count": len(candidates),
        "row_count": row_count,
        "status_counts": dict(sorted(status_counts.items())),
        "valid_candidate_count": sum(
            row["validation"] == "PASS" for row in candidates
        ),
        "finalized_count": sum(
            row["result"] == "PASS" for row in finalizations
        ),
        "batches": batches,
        "candidates": candidates,
        "finalizations": finalizations,
        "model_facing": model_facing,
    }


def probe(args: argparse.Namespace) -> dict[str, object]:
    output_root = args.output_dir.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    historical = probe_historical(args.m12cb_root.resolve(), output_root)
    fresh = probe_fresh(args.m12ce_root.resolve(), output_root)
    return {
        "contract": "m12cg-r2-valid-input-runtime-probe-v1",
        "runtime_label": args.runtime_label,
        "source_labels": {
            "historical": "packaged-source:m12cb",
            "fresh": "packaged-source:m12ce",
        },
        "historical": historical,
        "fresh": fresh,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m12cb-root", type=Path, required=True)
    parser.add_argument("--m12ce-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--runtime-label", required=True)
    args = parser.parse_args()
    result = probe(args)
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_bytes(pretty_bytes(result))


if __name__ == "__main__":
    main()
