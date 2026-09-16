from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from datetime import UTC, datetime
from pathlib import Path

from app.services.accepted_decision_v2_runtime_service import (
    STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT,
    AcceptedV2FundamentalCoreCandidate,
    AcceptedV2ProductionContext,
    accepted_v2_production_prompt,
    accepted_v2_stage2_output_schema,
    accepted_v2_stage2_ref_catalog_manifest,
    materialize_accepted_v2_stage2_output,
    validate_accepted_v2_production_output,
)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
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
    payload = json.loads(json.dumps(raw, ensure_ascii=False))
    for field in ("fundamental_cores", "candidates", "adjudications"):
        rows = payload.get(field)
        if isinstance(rows, list):
            payload[field] = [
                row
                for row in rows
                if isinstance(row, dict) and str(row.get("ticker")) in selected
            ]
    return payload


def write_bytes(path: Path, value: bytes) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)
    return {
        "path": path.name,
        "size": len(value),
        "sha256": sha256_bytes(value),
    }


def probe(args: argparse.Namespace) -> dict[str, object]:
    source_root = args.m12ce_root.resolve()
    raw_root = source_root / "raw" / "reproof-no-repair" / "us"
    output_root = args.output_dir.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    context = AcceptedV2ProductionContext.model_validate_json(
        (raw_root / "context.json").read_text(encoding="utf-8")
    )
    batch_results: list[dict[str, object]] = []
    target_results: list[dict[str, object]] = []
    for batch in range(1, 4):
        raw_path = raw_root / f"batch-{batch:02d}.output.json"
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        subjects = tuple(str(row["ticker"]) for row in raw["candidates"])
        batch_context = subset_context(context, subjects)
        cores = tuple(
            AcceptedV2FundamentalCoreCandidate.model_validate(row)
            for row in raw["fundamental_cores"]
        )
        prompt = accepted_v2_production_prompt(
            batch_context,
            fundamental_cores=cores,
            subjects=subjects,
        ).encode("utf-8")
        schema = (
            json.dumps(
                accepted_v2_stage2_output_schema(
                    batch_context,
                    subjects=subjects,
                    fundamental_cores=cores,
                ),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        catalog = (
            json.dumps(
                accepted_v2_stage2_ref_catalog_manifest(
                    batch_context,
                    subjects=subjects,
                    fundamental_cores=cores,
                ),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        batch_results.append(
            {
                "batch": batch,
                "subjects": list(subjects),
                "prompt": write_bytes(
                    output_root / f"batch-{batch:02d}.prompt.txt", prompt
                ),
                "schema": write_bytes(
                    output_root / f"batch-{batch:02d}.schema.json", schema
                ),
                "catalog": write_bytes(
                    output_root / f"batch-{batch:02d}.ref-catalog.json", catalog
                ),
            }
        )
        for ticker in ("GOOGL", "HUT"):
            if ticker not in subjects:
                continue
            one_context = subset_context(context, (ticker,))
            one_raw = subset_raw(raw, (ticker,))
            row: dict[str, object] = {
                "ticker": ticker,
                "source_batch": batch,
                "source_raw_sha256": sha256_bytes(raw_path.read_bytes()),
            }
            try:
                materializer_parameters = inspect.signature(
                    materialize_accepted_v2_stage2_output
                ).parameters
                if "normalized_contract" in materializer_parameters:
                    normalized = materialize_accepted_v2_stage2_output(
                        one_context,
                        one_raw,
                        normalized_contract=(
                            STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT
                        ),
                    )
                else:
                    normalized = materialize_accepted_v2_stage2_output(
                        one_context,
                        one_raw,
                    )
                normalized_payload = normalized.model_dump(mode="json")
                row["normalization"] = "PASS"
                row["normalized_sha256"] = sha256_bytes(
                    canonical_json_bytes(normalized_payload)
                )
                normalized_path = output_root / f"{ticker}.normalized.json"
                normalized_path.write_text(
                    json.dumps(
                        normalized_payload,
                        ensure_ascii=False,
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                row["normalized_path"] = normalized_path.name
                try:
                    artifact = validate_accepted_v2_production_output(
                        one_context,
                        normalized,
                        validated_at=datetime(2026, 9, 16, tzinfo=UTC),
                    )
                    artifact_payload = artifact.model_dump(mode="json")
                    artifact_path = output_root / f"{ticker}.artifact.json"
                    artifact_path.write_text(
                        json.dumps(
                            artifact_payload,
                            ensure_ascii=False,
                            indent=2,
                            sort_keys=True,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    row["finalization"] = "PASS"
                    row["artifact_sha256"] = sha256_bytes(
                        canonical_json_bytes(artifact_payload)
                    )
                    row["artifact_path"] = artifact_path.name
                except Exception as exc:  # audit captures exact production exception
                    row["finalization"] = "FAIL"
                    row["finalization_error_type"] = type(exc).__name__
                    row["finalization_error"] = str(exc)
            except Exception as exc:  # audit captures exact production exception
                row["normalization"] = "FAIL"
                row["normalization_error_type"] = type(exc).__name__
                row["normalization_error"] = str(exc)
                row["finalization"] = "NOT_RUN"
            target_results.append(row)
    return {
        "contract": "m12cg-r1-runtime-probe-v1",
        "runtime_label": args.runtime_label,
        "source_label": args.source_label,
        "batches": batch_results,
        "finalization_targets": target_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m12ce-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--runtime-label", required=True)
    parser.add_argument("--source-label", default="packaged-source:m12ce")
    args = parser.parse_args()
    result = probe(args)
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
