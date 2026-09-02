from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.ai_review_service import _validate_bound_ai_review_output
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.runtime_reasoning_ownership_service import (
    apply_candidate_ownership_contracts,
)
from app.services.semantic_decision_service import ensure_semantic_scope_contract
from app.services.working_capital_user_visible_preintegration_service import (
    ensure_relation_semantics,
    normalize_directional_numeric_refs,
)


CONTRACT = "four-track-daily-review-frozen-replay-v1"


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def replay(packet_path: Path, candidate_paths: list[Path]) -> dict[str, object]:
    packet = ensure_semantic_scope_contract(
        ensure_relation_semantics(_read(packet_path))
    )
    results: list[dict[str, object]] = []
    for candidate_path in candidate_paths:
        candidate = _read(candidate_path)
        directional, relation_report = normalize_directional_numeric_refs(
            packet,
            candidate,
        )
        normalized, ownership_report = apply_candidate_ownership_contracts(
            packet,
            directional,
        )
        binding = bind_numeric_fact_references(packet, normalized)
        typed = binding.report.get("typed_valuation_interpretations")
        typed_errors = (
            list(typed.get("errors", [])) if isinstance(typed, dict) else []
        )
        _, validation_errors = _validate_bound_ai_review_output(
            None,
            packet,
            binding.output,
            enforce_current_monitoring=False,
        )
        prior_validation_path = Path(f"{candidate_path}.validation.json")
        prior_validation = (
            _read(prior_validation_path) if prior_validation_path.is_file() else {}
        )
        results.append(
            {
                "candidate": candidate_path.name,
                "prior_error_count": len(prior_validation.get("errors", [])),
                "prior_errors": prior_validation.get("errors", []),
                "binding_errors": list(binding.errors),
                "validation_errors": validation_errors,
                "typed_valuation_errors": typed_errors,
                "relation_report": relation_report,
                "ownership_report": ownership_report,
                "status": (
                    "PASS"
                    if not binding.errors
                    and not validation_errors
                    and not typed_errors
                    else "FAIL"
                ),
            }
        )
    passed = all(result["status"] == "PASS" for result in results)
    return {
        "contract": CONTRACT,
        "packet_id": packet.get("packet_id"),
        "candidate_count": len(results),
        "results": results,
        "gates": {
            "daily_review_correction_changes_v2_accepted": 0,
            "daily_review_repair_loop_unbounded": 0,
            "daily_review_unbound_numeric_after_correction": 0,
            "market_breadth_authored_label_conflict": 0 if passed else None,
        },
        "status": "PASS" if passed else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = replay(args.packet, args.candidate)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
