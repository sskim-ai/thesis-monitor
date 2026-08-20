from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "reports" / "20260820-phase9-0b-canonical-facts.json"


def _evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_phase9_0b_active_universe_reproduces_architecture_coverage() -> None:
    evidence = _evidence()

    assert evidence["contract"] == "cash-flow-capital-efficiency-v1"
    assert len(evidence["active_universe"]) == 20
    assert evidence["metric_counts"] == {
        "ocf": {
            "ELIGIBLE": 12,
            "PARTIAL": 7,
            "BLOCKED": 1,
            "NOT_APPLICABLE": 0,
        },
        "capex_ppe": {
            "ELIGIBLE": 11,
            "PARTIAL": 6,
            "BLOCKED": 2,
            "NOT_APPLICABLE": 1,
        },
        "fcf": {
            "ELIGIBLE": 11,
            "PARTIAL": 0,
            "BLOCKED": 8,
            "NOT_APPLICABLE": 1,
        },
    }
    assert {item["category"] for item in evidence["coverage_drift"]} == {
        "UNCHANGED"
    }


def test_every_shadow_fcf_has_exact_reproducible_inputs() -> None:
    evidence = _evidence()
    facts = {item["fact_id"]: item for item in evidence["canonical_facts"]}
    fcf_facts = [
        item
        for item in evidence["canonical_facts"]
        if item["metric"] == "free_cash_flow_ppe"
    ]

    assert fcf_facts
    for fcf in fcf_facts:
        assert fcf["fact_type"] == "DERIVED_METRIC"
        assert fcf["derivation_formula"] == "OCF_MINUS_PPE_CAPEX_CASH_OUTFLOW"
        assert fcf["derivation_version"] == "cash-flow-capital-efficiency-v1"
        assert len(fcf["input_fact_ids"]) == 2
        ocf, capex = (facts[fact_id] for fact_id in fcf["input_fact_ids"])
        assert ocf["metric"] == "operating_cash_flow"
        assert capex["metric"] == "ppe_capex_cash_outflow"
        assert Decimal(fcf["value"]) == Decimal(ocf["value"]) - Decimal(capex["value"])
        for field in (
            "ticker",
            "issuer_id",
            "period_start",
            "period_end",
            "period_type",
            "currency",
            "unit",
            "entity_scope",
            "statement_basis",
            "source_document_id",
        ):
            assert ocf[field] == capex[field], (fcf["fact_id"], field)


def test_kr_and_insurance_remain_fail_closed() -> None:
    evidence = _evidence()
    records = {item["ticker"]: item for item in evidence["active_universe"]}

    for ticker in ("000660", "005490", "005930", "010120", "012450", "086280"):
        assert records[ticker]["metrics"]["fcf"]["status"] == "BLOCKED"
        assert records[ticker]["metrics"]["fcf"]["reason"] == (
            "period_context_unresolved"
        )
        assert records[ticker]["latest_safe_period"] is None
    assert records["003690"]["metrics"]["fcf"]["status"] == "NOT_APPLICABLE"
    assert not any(item["ticker"].isdigit() for item in evidence["canonical_facts"])


def test_foreign_issuer_facts_do_not_create_security_level_metrics() -> None:
    evidence = _evidence()
    metrics = {item["metric"] for item in evidence["canonical_facts"]}

    assert metrics == {
        "operating_cash_flow",
        "ppe_capex_cash_outflow",
        "free_cash_flow_ppe",
    }
    serialized = json.dumps(evidence["canonical_facts"], ensure_ascii=False).lower()
    for forbidden in ("fcf_yield", "fcf_per_share", "ev_fcf", "market_cap"):
        assert forbidden not in serialized


def test_readiness_has_no_open_p0_or_p1() -> None:
    evidence = _evidence()
    readiness = evidence["readiness"]

    assert readiness["p0_open"] == []
    assert readiness["p1_open"] == []
    assert readiness["phase_9_0c_ready"] is True
    assert readiness["phase_9_0c_scope"] == (
        "CASH_FLOW_SHADOW_CONSUMPTION_EARNINGS_QUALITY"
    )
    assert readiness["runtime_behavior_diff"] == 0
    assert evidence["deferred"] == {"ccc": True, "standard_roic": True}
    assert all(value == 0 for value in evidence["mutations"].values())
