from __future__ import annotations

# ruff: noqa: E402

import hashlib
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.cash_flow_capital_efficiency_service import Metric
from app.services.working_capital_runtime_shadow_canary_service import (
    ALLOWED_METRICS,
    CANARY_POLICY_VERSION,
    _numeric_binding_report,
    _quality_receipt,
    _runtime_scope,
    _snapshot,
)
from app.services.working_capital_shadow_consumption_service import (
    build_working_capital_reasoning_context,
    context_to_dict,
    reasoning_to_dict,
    render_working_capital_reasoning,
    validate_working_capital_reasoning,
)


REPORTS = ROOT / "docs" / "reports"
CORE_PATH = REPORTS / "20260821-phase9-1b-canonical-facts.json"
CONSUMPTION_PATH = REPORTS / "20260821-phase9-1c-shadow-context.json"
OUTPUT_PATH = REPORTS / "20260821-phase9-1d-readiness.json"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    core = _read(CORE_PATH)
    consumption = _read(CONSUMPTION_PATH)
    records = {str(item["ticker"]): item for item in core["active_universe"]}
    subjects: list[dict[str, Any]] = []
    reasonings = {}
    all_facts = {}
    all_relations = {}
    selector_errors: list[dict[str, str]] = []
    semantic_errors: list[dict[str, object]] = []

    for prior in consumption["subjects"]:
        ticker = str(prior["ticker"])
        previous = prior["context"]
        cutoff = date.fromisoformat(str(previous["cutoff"]))
        snapshot = _runtime_scope(_snapshot(records[ticker], as_of=cutoff))
        prior_unknowns = tuple(
            str(item) for item in prior.get("unknown_audit", {}).get("before", ())
        )
        context = build_working_capital_reasoning_context(
            snapshot,
            ticker=ticker,
            market=str(prior["market"]),
            packet_id=str(previous["packet_id"]),
            assessment_date=date.fromisoformat(str(previous["assessment_date"])),
            cutoff=cutoff,
            industry=str(prior["industry"]),
            monitoring_text=str(prior["before_text"]),
            existing_unknowns=prior_unknowns,
            latest_formal_balance_date=snapshot.latest_safe_working_capital_date,
            formal_lagging_provisional=(
                previous["freshness_state"] == "FORMAL_LAGGING_PROVISIONAL"
            ),
        )
        reasoning = render_working_capital_reasoning(context)
        reasonings[ticker] = reasoning
        facts = {item.fact_id: item for item in snapshot.canonical_facts}
        relations = {
            item.relation_id: item for item in snapshot.relations if item.relation_id
        }
        all_facts.update(facts)
        all_relations.update(relations)
        errors = validate_working_capital_reasoning(
            context, facts, relations, reasoning
        )
        if errors:
            semantic_errors.append({"ticker": ticker, "errors": list(errors)})

        prior_relations = previous.get("selected_relations") or []
        old_relation_id = (
            str(prior_relations[0]["relation_id"])
            if previous.get("shadow_used") and prior_relations
            else None
        )
        old_metric = (
            str(prior_relations[0]["balance_metric"])
            if previous.get("shadow_used") and prior_relations
            else None
        )
        old_in_scope = old_metric in {item.value for item in ALLOWED_METRICS}
        new_relation_id = (
            context.selected_relation.relation_id
            if context.shadow_used and context.selected_relation
            else None
        )
        if old_in_scope and old_relation_id != new_relation_id:
            selector_errors.append(
                {
                    "ticker": ticker,
                    "error": "approved_relation_parity_mismatch",
                }
            )
        if not old_in_scope and new_relation_id is not None:
            selector_errors.append(
                {"ticker": ticker, "error": "new_out_of_scope_selection"}
            )
        subjects.append(
            {
                "ticker": ticker,
                "market": prior["market"],
                "industry": prior["industry"],
                "retrospective_selected_relation": old_relation_id,
                "runtime_selected_relation": new_relation_id,
                "runtime_selected_metric": (
                    context.selected_relation.balance_metric.value
                    if context.shadow_used and context.selected_relation
                    else None
                ),
                "selector_parity": old_relation_id == new_relation_id,
                "context": context_to_dict(context),
                "reasoning": reasoning_to_dict(reasoning),
                "validation_errors": list(errors),
            }
        )

    binding = _numeric_binding_report(reasonings, all_relations, all_facts)
    quality = _quality_receipt(reasonings)
    selected = [item for item in subjects if item["runtime_selected_relation"]]
    metric_counts = Counter(item["runtime_selected_metric"] for item in selected)
    all_errors = len(selector_errors) + len(semantic_errors)
    ready = (
        all_errors == 0
        and binding["status"] == "passed"
        and quality["status"] == "passed"
        and set(metric_counts) <= {Metric.INVENTORY.value, Metric.TRADE_AR.value}
    )
    payload = {
        "contract": CANARY_POLICY_VERSION,
        "generated_at": "2026-08-21T00:00:00+00:00",
        "source_core": str(CORE_PATH.relative_to(ROOT)),
        "source_core_sha256": _sha(CORE_PATH),
        "source_consumption": str(CONSUMPTION_PATH.relative_to(ROOT)),
        "source_consumption_sha256": _sha(CONSUMPTION_PATH),
        "active_universe_count": len(subjects),
        "allowed_metrics": sorted(item.value for item in ALLOWED_METRICS),
        "selected_count": len(selected),
        "selected_metric_counts": dict(metric_counts),
        "selector_parity_errors": selector_errors,
        "semantic_errors": semantic_errors,
        "numeric_binding": binding,
        "quality": quality,
        "production_influence_count": 0,
        "telegram_change_count": 0,
        "production_ai_input_change_count": 0,
        "fallback_change_count": 0,
        "public_action_change_count": 0,
        "assessment_mutation_count": 0,
        "warning_mutation_count": 0,
        "natural_proof": {
            "inventory": "NOT_OBSERVED",
            "exact_trade_ar": "NOT_OBSERVED",
        },
        "phase_9_1d_deployment_candidate": ready,
        "phase_9_1e_architecture_ready": ready,
        "subjects": subjects,
    }
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
