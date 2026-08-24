from __future__ import annotations

from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.numeric_semantic_registry import (
    build_numeric_registry,
    numeric_registry_coverage,
)


def _positioning_fact(*, include_unknown: bool = False) -> dict[str, object]:
    reconciliations = {}
    for index, window in enumerate(("1d", "5d", "20d"), start=1):
        reconciliations[window] = {
            "constituent_count": index,
            "participant_flows": {
                "foreign": -100 * index,
                "institution": 50 * index,
                "individual": 25 * index,
                "other_corporation": 20 * index,
                "domestic_foreign": 5 * index,
            },
            "displayed_net": -25 * index,
            "omitted_net": 25 * index,
            "all_participant_net": 0,
            "display_coverage_ratio": 0.75,
        }
    if include_unknown:
        reconciliations["1d"]["reconciliation_difference"] = 7
    return {
        "fact_id": "positioning:2026-08-24",
        "fact_type": "positioning",
        "fields": {
            "foreign_net_buy_qty": -100,
            "institution_net_buy_qty": 50,
            "individual_net_buy_qty": 25,
            "foreign_net_buy_qty_5": -500,
            "institution_net_buy_qty_5": 250,
            "individual_net_buy_qty_5": 125,
            "foreign_net_buy_qty_20": -2_000,
            "institution_net_buy_qty_20": 1_000,
            "individual_net_buy_qty_20": 500,
            "reconciliations": reconciliations,
        },
    }


def test_reconciliation_registry_accounts_for_all_thirty_paths_as_internal() -> None:
    registry = build_numeric_registry([_positioning_fact()])
    reconciliation = [
        item
        for item in registry
        if str(item["field_path"]).startswith("fields.reconciliations.")
    ]
    coverage = numeric_registry_coverage([registry])

    assert len(reconciliation) == 30
    assert coverage["unsupported"] == []
    assert all(item["registered"] is True for item in reconciliation)
    assert all(item["prose_allowed"] is False for item in reconciliation)
    assert all(
        item["registry_class"] == "REGISTERED_INTERNAL_DERIVED"
        for item in reconciliation
    )
    assert all(item["audit_only"] is True for item in reconciliation)
    assert {item["window"] for item in reconciliation} == {"1d", "5d", "20d"}


def test_canonical_flow_remains_prose_eligible_but_reconciliation_copy_does_not() -> None:
    registry = build_numeric_registry([_positioning_fact()])
    canonical = next(
        item
        for item in registry
        if item["field_path"] == "fields.institution_net_buy_qty_5"
    )
    audit_copy = next(
        item
        for item in registry
        if item["field_path"]
        == "fields.reconciliations.5d.participant_flows.institution"
    )

    assert canonical["semantic_type"] == "institution_net_buy_qty_5d"
    assert canonical["prose_allowed"] is True
    assert canonical["allowed_sections"] == ["supply_analysis"]
    assert audit_copy["semantic_type"] == (
        "investor_flow_institution_net_buy_qty_5d_audit"
    )
    assert audit_copy["prose_allowed"] is False
    assert audit_copy["participant"] == "institution"


def test_audit_only_reconciliation_value_cannot_bind_into_prose() -> None:
    fact = _positioning_fact()
    packet = {
        "stocks": [
            {
                "ticker": "TEST",
                "numeric_registry": build_numeric_registry([fact]),
            }
        ]
    }
    output = {
        "stock_reviews": [
            {
                "ticker": "TEST",
                "facts_used": [fact["fact_id"]],
                "core_judgment": {"text": "{{numeric:audit}}"},
                "numeric_claims": [],
                "numeric_fact_refs": [
                    {
                        "ref_id": "audit",
                        "fact_id": fact["fact_id"],
                        "field_path": (
                            "fields.reconciliations.5d.participant_flows.institution"
                        ),
                        "text_ref": "core_judgment.text",
                    }
                ],
            }
        ]
    }

    result = bind_numeric_fact_references(packet, output)

    assert any("numeric_fact_ref_semantic_not_supported" in item for item in result.errors)


def test_wrong_window_participant_and_residual_paths_remain_fail_closed() -> None:
    registry = build_numeric_registry([_positioning_fact(include_unknown=True)])
    by_path = {str(item["field_path"]): item for item in registry}

    foreign_1d = by_path["fields.reconciliations.1d.participant_flows.foreign"]
    foreign_5d = by_path["fields.reconciliations.5d.participant_flows.foreign"]
    institution_1d = by_path[
        "fields.reconciliations.1d.participant_flows.institution"
    ]
    residual = by_path["fields.reconciliations.1d.reconciliation_difference"]

    assert foreign_1d["semantic_type"] != foreign_5d["semantic_type"]
    assert foreign_1d["semantic_type"] != institution_1d["semantic_type"]
    assert residual["registered"] is False
    assert residual["registry_class"] == "UNSUPPORTED_BLOCKING"
    assert numeric_registry_coverage([registry])["ready"] is False
