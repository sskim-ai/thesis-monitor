from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "reports" / "20260821-phase9-1b-canonical-facts.json"


def _evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_active_universe_implementation_matches_architecture_coverage() -> None:
    evidence = _evidence()

    assert evidence["contract"] == "working-capital-evidence-v1"
    assert evidence["active_universe_count"] == 20
    assert evidence["market_counts"] == {"KR": 7, "US_FOREIGN": 13}
    assert evidence["metric_counts"] == {
        "inventory": {"ELIGIBLE": 11, "PARTIAL": 3, "BLOCKED": 5, "NOT_APPLICABLE": 1},
        "trade_ar": {"ELIGIBLE": 6, "PARTIAL": 1, "BLOCKED": 12, "NOT_APPLICABLE": 1},
        "broad_ar": {"ELIGIBLE": 9, "PARTIAL": 3, "BLOCKED": 7, "NOT_APPLICABLE": 1},
        "trade_ap": {"ELIGIBLE": 8, "PARTIAL": 1, "BLOCKED": 10, "NOT_APPLICABLE": 1},
        "broad_ap": {"ELIGIBLE": 10, "PARTIAL": 1, "BLOCKED": 8, "NOT_APPLICABLE": 1},
    }
    assert evidence["coverage_drift"]["newly_blocked"] == []
    assert evidence["coverage_drift"]["recovered"] == []


def test_every_eligible_derived_fact_is_reproducible() -> None:
    evidence = _evidence()

    for record in evidence["active_universe"]:
        facts = {item["fact_id"]: item for item in record["canonical_facts"]}
        for fact in facts.values():
            if fact["fact_type"] != "DERIVED_METRIC":
                continue
            assert len(fact["input_fact_ids"]) == 2
            assert set(fact["input_fact_ids"]) <= facts.keys()
            current, prior = (facts[item] for item in fact["input_fact_ids"])
            if fact["metric"] == "working_capital_balance_delta":
                expected = Decimal(current["value"]) - Decimal(prior["value"])
            else:
                expected = (
                    (Decimal(current["value"]) - Decimal(prior["value"]))
                    / Decimal(prior["value"])
                    * Decimal(100)
                )
            assert Decimal(fact["value"]) == expected


def test_every_eligible_relation_has_complete_structured_lineage() -> None:
    evidence = _evidence()

    for record in evidence["active_universe"]:
        facts = {item["fact_id"]: item for item in record["canonical_facts"]}
        for relation in record["relations"].values():
            if relation["status"] != "ELIGIBLE":
                continue
            assert relation["relation_type"] == "YOY_GROWTH_COMPARISON"
            assert relation["direction"] in {"GREATER", "LOWER", "EQUAL"}
            assert len(relation["input_fact_ids"]) == 6
            assert set(relation["input_fact_ids"]) <= facts.keys()
            balance_yoy = facts[relation["balance_yoy_fact_id"]]
            flow_yoy = facts[relation["flow_yoy_fact_id"]]
            assert balance_yoy["metric"] == "working_capital_balance_yoy_growth"
            assert flow_yoy["metric"] == "financial_flow_yoy_growth"
            assert Decimal(relation["gap_percentage_points"]) == (
                Decimal(balance_yoy["value"]) - Decimal(flow_yoy["value"])
            )


def test_trade_and_broad_semantics_survive_relation_identity() -> None:
    evidence = _evidence()

    for record in evidence["active_universe"]:
        pairs = (
            ("trade_ar_vs_revenue", "broad_ar_vs_revenue"),
            ("trade_ap_vs_cogs", "broad_ap_vs_cogs"),
        )
        for trade_key, broad_key in pairs:
            trade = record["relations"][trade_key]
            broad = record["relations"][broad_key]
            if trade["status"] == broad["status"] == "ELIGIBLE":
                assert trade["relation_id"] != broad["relation_id"]
                assert trade["balance_metric"] != broad["balance_metric"]
                assert trade["balance_semantic"] != broad["balance_semantic"]


def test_kr_balance_core_and_insurance_negative_control() -> None:
    records = {item["ticker"]: item for item in _evidence()["active_universe"]}

    for ticker in ("000660", "005490", "005930", "010120", "012450", "086280"):
        assert records[ticker]["metrics"]["inventory"]["status"] == "ELIGIBLE"
        assert records[ticker]["latest_safe_working_capital_date"] == "2026-06-30"
        assert records[ticker]["source_audit"]["cash_flow_period_gap_independent"] is True
    assert records["003690"]["industry_status"] == "NOT_APPLICABLE"
    assert records["003690"]["canonical_facts"] == []
    assert all(
        relation["status"] == "NOT_APPLICABLE"
        for relation in records["003690"]["relations"].values()
    )


def test_lineage_idempotency_provider_and_readiness_gates() -> None:
    evidence = _evidence()
    lineage = evidence["lineage_audit"]
    provider = evidence["provider_telemetry"]
    readiness = evidence["readiness"]

    assert lineage["counts"] == {
        "reported_raw_facts": 160,
        "derived_facts": 119,
        "working_capital_balance_delta": 44,
        "working_capital_balance_yoy_growth": 44,
        "financial_flow_yoy_growth": 31,
        "eligible_relations": 53,
    }
    assert lineage["all_errors"] == []
    assert lineage["idempotency_errors"] == []
    assert provider["sec_companyfacts"] == {
        "stored_cache_hits": 13,
        "live_requests": 0,
        "failures": 0,
    }
    assert provider["opendart"] == {
        "stored_cache_hits": 12,
        "live_requests": 0,
        "failures": 0,
    }
    assert provider["new_paid_providers"] == 0
    assert readiness["p0_open"] == []
    assert readiness["p1_open"] == []
    assert readiness["phase_9_1c_ready"] is True
    assert readiness["phase_9_1c_scope"] == (
        "WORKING_CAPITAL_SHADOW_CONSUMPTION_EARNINGS_QUALITY"
    )
    assert readiness["runtime_user_visible_diff"] == 0
    assert set(readiness["advanced_ratios"].values()) == {"DEFER"}
    assert all(value == 0 for value in evidence["mutations"].values())
