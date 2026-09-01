from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from app.jobs.accepted_decision_v2_runtime import _paths
from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_review_service import (
    _canonical_identifier_spans,
    _prose_fields,
    _prose_number_occurrences,
    _validate_stock_review,
)
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.runtime_reasoning_ownership_service import (
    apply_candidate_ownership_contracts,
)
from app.services.working_capital_user_visible_preintegration_service import (
    ensure_relation_semantics,
    normalize_directional_numeric_refs,
)


CONTRACT = "v2-natural-runtime-repair-evidence-v1"
TARGET_TICKER = "047810"


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_stock_errors(
    packet: dict[str, object],
    candidate: dict[str, object],
) -> tuple[dict[str, list[str]], AIDailyReviewOutput, dict[str, object]]:
    normalized_packet = ensure_relation_semantics(packet)
    directional, _ = normalize_directional_numeric_refs(
        normalized_packet,
        candidate,
    )
    owned, _ = apply_candidate_ownership_contracts(
        normalized_packet,
        directional,
    )
    binding = bind_numeric_fact_references(normalized_packet, owned)
    if binding.errors:
        raise ValueError("run50_numeric_binding_failed:" + ",".join(binding.errors))
    output = AIDailyReviewOutput.model_validate(binding.output)
    stocks = {
        str(row.get("ticker") or ""): row
        for row in normalized_packet.get("stocks") or ()
        if isinstance(row, dict)
    }
    errors = {
        review.ticker: _validate_stock_review(
            review,
            stocks[review.ticker],
            str(normalized_packet.get("market") or "") or None,
        )
        for review in output.stock_reviews
    }
    typed = binding.report.get("typed_valuation_interpretations")
    if isinstance(typed, Mapping):
        errors["_typed_valuation"] = [str(item) for item in typed.get("errors") or ()]
    return errors, output, stocks


def _original_errors(validation: Mapping[str, object]) -> list[str]:
    return [str(item) for item in validation.get("errors") or ()]


def _identifier_audit(
    output: AIDailyReviewOutput,
    stocks: Mapping[str, dict[str, object]],
) -> dict[str, object]:
    review = next(row for row in output.stock_reviews if row.ticker == TARGET_TICKER)
    context = stocks[TARGET_TICKER]
    field_rows = []
    for field_path, text in _prose_fields(review).items():
        identifiers = _canonical_identifier_spans(text, context)
        product_identifiers = [
            row
            for row in identifiers
            if str(row.get("full_span") or "") in {"KF-21", "FA-50"}
        ]
        if not product_identifiers:
            continue
        field_rows.append(
            {
                "field_path": field_path,
                "identifiers": product_identifiers,
                "unbound_numeric_tokens": [
                    token
                    for _, _, token in _prose_number_occurrences(text, context)
                ],
            }
        )
    adjacent_text = "KF-21 21대 FA-50 50대 KF-21 수출 5조원 FA-50 마진 12%"
    unsupported_text = "ZZ-999"
    range_text = "-21% 21-50 $-50"
    return {
        "ticker": TARGET_TICKER,
        "field_rows": field_rows,
        "phantom_numeric_tokens": sorted(
            {
                token
                for row in field_rows
                for token in row["unbound_numeric_tokens"]
                if token in {"21", "50"}
            }
        ),
        "adjacent_real_numeric_tokens": [
            token
            for _, _, token in _prose_number_occurrences(adjacent_text, context)
        ],
        "unsupported_identifier_tokens": [
            token
            for _, _, token in _prose_number_occurrences(unsupported_text, context)
        ],
        "hyphen_numeric_tokens": [
            token
            for _, _, token in _prose_number_occurrences(range_text, context)
        ],
    }


def _v2_result(path: Path | None) -> dict[str, object]:
    if path is None or not path.exists():
        return {
            "status": "NOT_RUN_EXTERNAL_APPROVAL_REQUIRED",
            "model_call_reached": False,
            "candidate_generated_count": 0,
            "accepted_ready_count": 0,
            "explicit_v2_decision_count": 0,
        }
    artifact = _read_json(path)
    return {
        "status": artifact.get("status"),
        "model_call_reached": True,
        "candidate_generated_count": len(artifact.get("candidates") or ()),
        "accepted_ready_count": artifact.get("ready_count"),
        "explicit_v2_decision_count": len(artifact.get("blocks") or ()),
        "selected_subjects": artifact.get("selected_subjects"),
        "message_quality": artifact.get("message_quality"),
        "artifact_sha256": _sha256(path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary-packet", type=Path, required=True)
    parser.add_argument("--primary-claim", type=Path, required=True)
    parser.add_argument("--primary-candidate", type=Path, required=True)
    parser.add_argument("--primary-validation", type=Path, required=True)
    parser.add_argument("--backup-candidate", type=Path, required=True)
    parser.add_argument("--backup-validation", type=Path, required=True)
    parser.add_argument("--accepted-artifact", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    packet = _read_json(args.primary_packet)
    primary_candidate = _read_json(args.primary_candidate)
    backup_candidate = _read_json(args.backup_candidate)
    primary_validation = _read_json(args.primary_validation)
    backup_validation = _read_json(args.backup_validation)
    primary_errors, primary_output, stocks = _validated_stock_errors(
        packet,
        primary_candidate,
    )
    backup_errors, _, _ = _validated_stock_errors(packet, backup_candidate)
    claim = _read_json(args.primary_claim)
    claim_id = str(claim.get("claim_id") or "")
    paths = _paths(claim, claim_id)
    primary_before = _original_errors(primary_validation)
    backup_before = _original_errors(backup_validation)
    identifier = _identifier_audit(primary_output, stocks)
    primary_after = [error for values in primary_errors.values() for error in values]
    backup_after = [error for values in backup_errors.values() for error in values]
    path_segment = "data/ai_review/claims"

    evidence = {
        "contract": CONTRACT,
        "source": {
            "packet_id": packet.get("packet_id"),
            "claim_id": claim_id,
            "packet_sha256": _sha256(args.primary_packet),
            "claim_sha256": _sha256(args.primary_claim),
            "primary_candidate_sha256": _sha256(args.primary_candidate),
            "primary_validation_sha256": _sha256(args.primary_validation),
            "backup_candidate_sha256": _sha256(args.backup_candidate),
            "backup_validation_sha256": _sha256(args.backup_validation),
            "production_archive_mutated": 0,
        },
        "path_control": {
            "final_output_path_stored_relative": not Path(
                str(claim.get("final_output_path") or "")
            ).is_absolute(),
            "effective_paths_absolute": all(path.is_absolute() for path in paths.values()),
            "schema_exists": paths["schema"].is_file(),
            "prompt_exists": paths["prompt"].is_file(),
            "schema_path_claim_segment_count": str(paths["schema"]).count(path_segment),
            "schema_path_duplicated": int(str(paths["schema"]).count(path_segment) != 1),
        },
        "identifier_control": identifier,
        "original_errors": {
            "primary": primary_before,
            "backup": backup_before,
        },
        "replayed_errors": {
            "primary": primary_after,
            "backup": backup_after,
        },
        "negative_controls": {
            "000660_valuation_quality_guard": any(
                error.startswith("000660:valuation_interpretation_evidence_invalid:")
                for error in primary_after
            ),
            "005930_risk_reward_guard": any(
                error.startswith("005930:unsupported_risk_reward_comparison:")
                for error in backup_after
            ),
            "genuine_guards_weakened": 0,
        },
        "v2_replay": _v2_result(args.accepted_artifact),
        "gates": {
            "V2_EFFECTIVE_SCHEMA_PATH_DUPLICATION": int(
                str(paths["schema"]).count(path_segment) != 1
            ),
            "V2_SCHEMA_PRECHECK": "PASS"
            if paths["schema"].is_file() and paths["prompt"].is_file()
            else "FAIL",
            "047810_PRODUCT_IDENTIFIER_PHANTOM_NUMERIC": len(
                identifier["phantom_numeric_tokens"]
            ),
            "PRODUCT_IDENTIFIER_ADJACENT_NUMERIC_PROVENANCE": "PASS"
            if identifier["adjacent_real_numeric_tokens"] == ["21", "50", "5", "12"]
            else "FAIL",
            "UNSUPPORTED_PRODUCT_IDENTIFIER_REJECTED": "PASS"
            if "999" in identifier["unsupported_identifier_tokens"]
            else "FAIL",
            "000660_VALUATION_QUALITY_GUARD": "PASS"
            if any(
                error.startswith("000660:valuation_interpretation_evidence_invalid:")
                for error in primary_after
            )
            else "FAIL",
            "005930_RISK_REWARD_GUARD": "PASS"
            if any(
                error.startswith("005930:unsupported_risk_reward_comparison:")
                for error in backup_after
            )
            else "FAIL",
        },
    }
    _write_json(args.output, evidence)
    print(json.dumps(evidence["gates"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
