from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from app.services.ai_review_service import (
    _refresh_market_numeric_registry,
    _validate_bound_ai_review_output,
)
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.runtime_reasoning_ownership_service import (
    apply_candidate_ownership_contracts,
)
from app.services.semantic_decision_service import ensure_semantic_scope_contract
from app.services.working_capital_user_visible_preintegration_service import (
    ensure_relation_semantics,
    normalize_directional_numeric_refs,
)


EXPECTED_CANDIDATE_SHA256 = (
    "29dd96d0b9c1efec9d23a6c22fab1b02b3b92f65a28af71f01abf8b119757a7b"
)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _classify(error: str) -> str:
    if "holder_decision_variable_missing" in error or (
        error.startswith("MU:valuation_interpretation_occurrence_uncovered")
    ):
        return "VALIDATOR_FALSE_POSITIVE"
    if "working_capital_owner_mismatch" in error:
        return "SCHEMA_OWNERSHIP_MISMATCH"
    if error.startswith(("CRCL:", "GOOGL:", "HUT:", "IBM:", "SNDK:", "TSLA:")) and (
        "valuation_interpretation_metric_evidence_mismatch" in error
        or "valuation_interpretation_numeric_occurrence_uncovered" in error
    ):
        return "SCHEMA_OWNERSHIP_MISMATCH"
    if error.startswith("MU:") and "valuation_interpretation_" in error:
        return "SCHEMA_OWNERSHIP_MISMATCH"
    if error.startswith("SKHY:valuation_interpretation_occurrence_uncovered"):
        return "CORRECTION_CONTEXT_DEFECT"
    if error.startswith("market_review:"):
        return "PROVENANCE_BINDING_DEFECT"
    return "OTHER"


def replay(
    packet: dict[str, object], candidate: dict[str, object]
) -> dict[str, object]:
    packet = ensure_semantic_scope_contract(ensure_relation_semantics(packet))
    _refresh_market_numeric_registry(packet)
    directional, relation_report = normalize_directional_numeric_refs(packet, candidate)
    normalized, ownership_report = apply_candidate_ownership_contracts(packet, directional)
    binding = bind_numeric_fact_references(packet, normalized)
    typed_errors = list(
        (binding.report.get("typed_valuation_interpretations") or {}).get("errors") or []
    )
    validation_errors: list[str] = []
    accepted = False
    if not binding.errors:
        output, validation_errors = _validate_bound_ai_review_output(
            None,
            packet,
            binding.output,
            enforce_current_monitoring=False,
        )
        accepted = output is not None and not validation_errors and not typed_errors
    errors = list(dict.fromkeys([*binding.errors, *validation_errors, *typed_errors]))
    return {
        "accepted": accepted,
        "errors": errors,
        "error_count": len(errors),
        "binding_errors": list(binding.errors),
        "typed_errors": typed_errors,
        "validation_errors": validation_errors,
        "ownership_status": ownership_report.get("status"),
        "ownership_unresolved": ownership_report.get("unresolved"),
        "relation_report": relation_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay the frozen run-55 validator incident")
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    args = parser.parse_args()

    candidate_bytes = args.candidate.read_bytes()
    candidate_sha256 = hashlib.sha256(candidate_bytes).hexdigest()
    validation = _read(args.validation)
    original_errors = [str(value) for value in validation.get("errors", [])]
    classified = [
        {"index": index, "error": error, "classification": _classify(error)}
        for index, error in enumerate(original_errors, start=1)
    ]
    result = {
        "contract": "us-validator-22-frozen-replay-v1",
        "candidate_sha256": candidate_sha256,
        "candidate_sha256_matches": candidate_sha256 == EXPECTED_CANDIDATE_SHA256,
        "original_error_count": len(original_errors),
        "classified_error_count": len(classified),
        "classification": classified,
        "repaired_replay": replay(_read(args.packet), json.loads(candidate_bytes)),
        "model_rerun": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["candidate_sha256_matches"] and result["repaired_replay"]["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
