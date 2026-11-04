from copy import deepcopy
from datetime import date
import json

import pytest

from app.models.event import Event
from app.services.financial_validation import validate_event_financials
from app.services.financial_observation_quality_service import _anomaly_result
from test_financial_observation_quality import snapshots, evaluate, mutate_lineage


def event(**values):
    return Event(ticker="UNSEEN", date=date(2026, 8, 14), source="OpenDART",
                 provider="opendart", title="Manufacturer reported results", url="",
                 confirmed_facts=json.dumps(["OpenDART financial fact: 영업이익=120 KRW"]),
                 operating_income=120, net_income=130, **values)


@pytest.mark.parametrize("values,state", [({}, "UNAVAILABLE"), ({"revenue": None}, "UNAVAILABLE"),
    ({"revenue": 0}, "ZERO"), ({"revenue": -100}, "NEGATIVE"), ({"revenue": 100}, "POSITIVE")])
def test_distinct_denominator_states(values, state):
    result = validate_event_financials(event(**values))
    assert result.revenue_denominator["state"] == state
    assert result.revenue_denominator["value"] == values.get("revenue")
    if state == "POSITIVE":
        assert result.revenue_denominator["ratio_status"] == "EVALUABLE"
        assert set(result.soft_outliers) == {"operating_income_exceeds_revenue",
            "net_income_exceeds_revenue", "unusually_high_or_low_operating_margin"}
    else:
        assert result.revenue_denominator["ratio_status"] == "NOT_EVALUABLE"
        assert result.soft_outliers == []
    assert ("non_positive_revenue" in result.hard_errors) == (state in ("ZERO", "NEGATIVE"))


def test_reported_margin_with_missing_denominator_is_not_validated():
    result = validate_event_financials(event(operating_margin=800))
    assert result.revenue_denominator["ratio_status"] == "NOT_EVALUABLE"
    assert not result.soft_outliers


def test_legitimate_revenue_still_checks_reported_margin():
    result = validate_event_financials(event(revenue=1000, operating_margin=50))
    assert "reported_and_derived_margin_mismatch" in result.hard_errors


def test_unrelated_financial_services_case_is_not_manufacturing_margin():
    e = event(revenue=100)
    e.company_name = "Fictional Financial Bank"
    result = validate_event_financials(e)
    assert result.revenue_denominator["sector_ratio_applicable"] is False
    assert result.revenue_denominator["ratio_status"] == "NOT_EVALUABLE"
    assert not result.soft_outliers


def test_real_small_denominator_is_not_treated_as_missing():
    result = validate_event_financials(event(revenue=1))
    assert result.revenue_denominator["value"] == 1
    assert "operating_income_exceeds_revenue" in result.soft_outliers


def test_actual_occurrences_do_not_inject_a_sentinel():
    formal, _ = snapshots()
    result = _anomaly_result(formal, dict(revenue=None,
        operating_income={"amount": "675794814040"}, net_income={"amount": "488224283447"}))
    assert result.revenue_denominator["state"] == "UNAVAILABLE"
    assert result.soft_outliers == []


def test_all_missing_occurrences_are_explicitly_not_evaluable():
    formal, _ = snapshots()
    result = _anomaly_result(formal, dict(revenue=None, operating_income=None, net_income=None))
    assert result.revenue_denominator["state"] == "UNAVAILABLE"
    assert result.revenue_denominator["ratio_status"] == "NOT_EVALUABLE"
    assert not result.soft_outliers


def without_revenue():
    formal, _ = snapshots()
    formal.revenue = None
    formal.operating_margin = None
    formal.financial_soft_outliers = "[]"
    formal.raw_financial_fields = json.dumps([r for r in json.loads(formal.raw_financial_fields)
                                             if r["logical_field"] != "revenue"])
    return formal


def test_missing_revenue_is_local_not_an_independent_amount_denial():
    formal = without_revenue()
    before = deepcopy(formal.model_dump())
    q = evaluate(formal, None)
    assert q["fields"]["current.revenue"]["state"] == "denied"
    assert q["fields"]["current.operating_margin"]["state"] == "denied"
    assert q["fields"]["current.operating_income"]["state"] == "verified_usable"
    assert q["fields"]["current.net_income"]["state"] == "verified_usable"
    assert q["denominator_evaluation"]["current"]["ratio_status"] == "NOT_EVALUABLE"
    assert [c["metric"] for c in q["comparative_observations"]] == ["operating_income"]
    assert formal.model_dump() == before


def test_historical_outlier_is_not_silently_erased():
    formal = without_revenue()
    formal.financial_soft_outliers = '["unusually_high_or_low_operating_margin"]'
    q = evaluate(formal, None)
    assert q["fields"]["current.operating_income"]["state"] == "denied"
    assert "extreme_observation_uncorroborated" in q["fields"]["current.operating_income"]["hard_denial_reasons"]


@pytest.mark.parametrize("key,value", [("fs_div", "OFS"), ("source_filing", "20260814000009"),
    ("amount_period_start", "2026-01-01"), ("source_provider", "other"), ("amount", 1)])
def test_unqualified_denominator_never_contaminates_other_fields(key, value):
    formal, _ = snapshots()
    formal.financial_soft_outliers = "[]"
    mutate_lineage(formal, "revenue", key, value)
    q = evaluate(formal, None)
    assert q["denominator_evaluation"]["current"]["ratio_status"] == "NOT_EVALUABLE"
    assert q["fields"]["current.revenue"]["state"] == "denied"
    assert q["fields"]["current.operating_income"]["state"] == "verified_usable"


def test_incompatible_event_statement_basis_blocks_ratios():
    e = event(revenue=1)
    e.confirmed_facts = json.dumps([
        "OpenDART financial fact: 매출액=1 KRW (fs_div=CFS; sj_div=CIS; period_scope=quarter)",
        "OpenDART financial fact: 영업이익=120 KRW (fs_div=OFS; sj_div=CIS; period_scope=quarter)"])
    result = validate_event_financials(e)
    assert "inconsistent_statement_or_period_basis" in result.hard_errors
    assert result.revenue_denominator["ratio_status"] == "NOT_EVALUABLE"
    assert result.soft_outliers == []
