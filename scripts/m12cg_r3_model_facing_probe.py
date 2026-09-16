from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2FundamentalCoreCandidate,
    AcceptedV2ProductionContext,
    accepted_v2_production_prompt,
    accepted_v2_stage2_output_schema,
    accepted_v2_stage2_ref_catalog_manifest,
)


def pretty_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def raw_root(source_root: Path) -> Path:
    candidates = list(source_root.rglob("raw/reproof-no-repair/us/context.json"))
    if len(candidates) != 1:
        raise ValueError(f"m12ce_raw_root_ambiguous:{len(candidates)}")
    return candidates[0].parent


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


def run_probe(args: argparse.Namespace) -> None:
    source = raw_root(args.source_m12ce.resolve())
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    context = AcceptedV2ProductionContext.model_validate_json(
        (source / "context.json").read_text(encoding="utf-8")
    )
    rows: list[dict[str, object]] = []
    for batch_number in range(1, 4):
        raw = json.loads(
            (source / f"batch-{batch_number:02d}.output.json").read_text(
                encoding="utf-8"
            )
        )
        if not isinstance(raw, Mapping):
            raise ValueError(f"batch_output_invalid:{batch_number}")
        candidates = raw.get("candidates")
        cores_raw = raw.get("fundamental_cores")
        if not isinstance(candidates, list) or not isinstance(cores_raw, list):
            raise ValueError(f"batch_rows_invalid:{batch_number}")
        subjects = tuple(
            str(row["ticker"]) for row in candidates if isinstance(row, Mapping)
        )
        batch_context = subset_context(context, subjects)
        cores = tuple(
            AcceptedV2FundamentalCoreCandidate.model_validate(row)
            for row in cores_raw
        )
        payloads = {
            "prompt": accepted_v2_production_prompt(
                batch_context,
                fundamental_cores=cores,
                subjects=subjects,
            ).encode("utf-8"),
            "schema": pretty_bytes(
                accepted_v2_stage2_output_schema(
                    batch_context,
                    subjects=subjects,
                    fundamental_cores=cores,
                )
            ),
            "catalog": pretty_bytes(
                accepted_v2_stage2_ref_catalog_manifest(
                    batch_context,
                    subjects=subjects,
                    fundamental_cores=cores,
                )
            ),
        }
        for kind, payload in payloads.items():
            suffix = {
                "prompt": "prompt.txt",
                "schema": "schema.json",
                "catalog": "ref-catalog.json",
            }[kind]
            relative = f"batch-{batch_number:02d}.{suffix}"
            (out / relative).write_bytes(payload)
            rows.append(
                {
                    "batch": batch_number,
                    "subjects": list(subjects),
                    "kind": kind,
                    "path": relative,
                    "size": len(payload),
                    "sha256": sha256_bytes(payload),
                }
            )
    (out / "manifest.json").write_bytes(
        pretty_bytes(
            {
                "contract": "m12cg-r3-model-facing-builder-probe-v1",
                "runtime_label": args.runtime_label,
                "artifact_count": len(rows),
                "artifacts": rows,
                "status": "PASS" if len(rows) == 9 else "FAIL",
            }
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-m12ce", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--runtime-label", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    run_probe(parse_args())
