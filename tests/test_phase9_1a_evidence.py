from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "reports" / "20260821-phase9-1a-coverage.json"


def _evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_active_universe_and_metric_coverage_are_evidence_driven() -> None:
    evidence = _evidence()

    assert evidence["contract"] == "working-capital-evidence-v1"
    assert evidence["active_universe_count"] == 20
    assert evidence["market_counts"] == {"KR": 7, "US_FOREIGN": 13}
    assert evidence["metric_counts"] == {
        "inventory": {
            "ELIGIBLE": 11,
            "PARTIAL": 3,
            "BLOCKED": 5,
            "NOT_APPLICABLE": 1,
        },
        "trade_ar": {
            "ELIGIBLE": 6,
            "PARTIAL": 1,
            "BLOCKED": 12,
            "NOT_APPLICABLE": 1,
        },
        "broad_ar": {
            "ELIGIBLE": 9,
            "PARTIAL": 3,
            "BLOCKED": 7,
            "NOT_APPLICABLE": 1,
        },
        "trade_ap": {
            "ELIGIBLE": 8,
            "PARTIAL": 1,
            "BLOCKED": 10,
            "NOT_APPLICABLE": 1,
        },
        "broad_ap": {
            "ELIGIBLE": 10,
            "PARTIAL": 1,
            "BLOCKED": 8,
            "NOT_APPLICABLE": 1,
        },
    }


def test_every_eligible_movement_has_exact_reproducible_fact_inputs() -> None:
    evidence = _evidence()

    for record in evidence["active_universe"]:
        facts = {item["fact_id"]: item for item in record["facts"]}
        for key in ("inventory", "trade_ar", "broad_ar", "trade_ap", "broad_ap"):
            movement = record[key]
            if movement["status"] != "ELIGIBLE":
                continue
            current = facts[movement["current_fact_id"]]
            prior = facts[movement["prior_fact_id"]]
            assert current["period_type"] == prior["period_type"] == "POINT_IN_TIME"
            assert current["metric"] == prior["metric"]
            assert current["semantic_mapping"] == prior["semantic_mapping"]
            assert current["currency"] == prior["currency"]
            assert current["unit"] == prior["unit"]
            assert current["entity_scope"] == prior["entity_scope"]
            assert current["statement_basis"] == prior["statement_basis"]
            delta = Decimal(current["value"]) - Decimal(prior["value"])
            assert Decimal(movement["absolute_delta"]) == delta
            assert Decimal(movement["yoy_pct"]) == (
                delta / Decimal(prior["value"]) * Decimal(100)
            )


def test_every_eligible_cross_relation_has_four_fact_refs_and_no_verdict() -> None:
    evidence = _evidence()
    allowed_prefixes = ("AR_GROWTH_", "INVENTORY_GROWTH_", "AP_GROWTH_")

    for record in evidence["active_universe"]:
        fact_ids = {item["fact_id"] for item in record["facts"]}
        for relation in record["relations"].values():
            if relation["status"] != "ELIGIBLE":
                continue
            assert len(relation["input_fact_ids"]) == 4
            assert set(relation["input_fact_ids"]) <= fact_ids
            assert relation["formula"] == "BALANCE_YOY_PCT_MINUS_FLOW_YOY_PCT"
            assert relation["relation_type"].startswith(allowed_prefixes)
            assert "GOOD" not in relation["relation_type"]
            assert "BAD" not in relation["relation_type"]


def test_kr_balance_evidence_is_safe_despite_cash_flow_period_gap() -> None:
    records = {item["ticker"]: item for item in _evidence()["active_universe"]}

    for ticker in ("000660", "005490", "005930", "010120", "012450", "086280"):
        assert records[ticker]["inventory"]["status"] == "ELIGIBLE"
        assert records[ticker]["latest_formal_balance_date"] == "2026-06-30"
        assert records[ticker]["source_audit"]["basis"] == "CFS"
        assert records[ticker]["source_audit"]["cash_flow_period_gap_independent"] is True
    assert records["003690"]["inventory"]["status"] == "NOT_APPLICABLE"


def test_trade_and_broad_semantics_are_never_collapsed() -> None:
    evidence = _evidence()

    for record in evidence["active_universe"]:
        facts = record["facts"]
        trade_ar = {
            item["fact_id"]
            for item in facts
            if item["metric"] == "trade_accounts_receivable"
        }
        broad_ar = {
            item["fact_id"]
            for item in facts
            if item["metric"] == "accounts_receivable_broad"
        }
        trade_ap = {
            item["fact_id"]
            for item in facts
            if item["metric"] == "trade_accounts_payable"
        }
        broad_ap = {
            item["fact_id"]
            for item in facts
            if item["metric"] == "accounts_payable_broad"
        }
        assert trade_ar.isdisjoint(broad_ar)
        assert trade_ap.isdisjoint(broad_ap)


def test_provider_calls_and_deferred_advanced_ratios_are_explicit() -> None:
    evidence = _evidence()
    provider = evidence["provider_telemetry"]

    assert provider["sec_companyfacts"] == {
        "stored_cache_hits": 13,
        "cache_misses": 0,
        "live_requests": 0,
    }
    assert provider["opendart"]["acquisition"]["requests"] == 12
    assert provider["opendart"]["acquisition"]["successes"] == 12
    assert provider["opendart"]["acquisition"]["failures"] == []
    assert provider["new_paid_providers"] == 0
    assert evidence["deferred"] == {
        "dso": True,
        "inventory_days": True,
        "dpo": True,
        "ccc": True,
    }


def test_readiness_scope_and_zero_runtime_mutations() -> None:
    evidence = _evidence()
    readiness = evidence["readiness"]
    decisions = evidence["architecture_decisions"]

    assert decisions["ar_initial_scope"] == "TRADE_PLUS_SEPARATE_BROAD"
    assert decisions["ap_initial_scope"] == "TRADE_PLUS_SEPARATE_BROAD"
    assert readiness["p0_open"] == []
    assert readiness["p1_open"] == []
    assert readiness["phase_9_1b_ready"] is True
    assert readiness["phase_9_1b_scope"] == (
        "SELECTIVE_INVENTORY_AR_AP_CANONICAL_CORE"
    )
    assert readiness["runtime_user_visible_diff"] == 0
    assert all(value == 0 for value in evidence["mutations"].values())
