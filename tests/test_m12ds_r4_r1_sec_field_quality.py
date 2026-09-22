import json
from datetime import date

import pytest

from app.services.sec_business_field_quality_service import field_errors, reported_comparison_quality
from app.services.sec_financial_snapshot_service import _companyfacts_snapshots
from app.services.valuation_snapshot_service import _earnings_quarters
from tests.test_external_api_accuracy import _companyfact_entry, _companyfacts_payload


def fixture(ticker="RENAMED"):
    current = _companyfact_entry(30, fp="Q2", start="2026-04-01", end="2026-06-30", filed="2026-08-01")
    prior = dict(current, start="2025-04-01", end="2025-06-30", val=-20)
    payload = _companyfacts_payload("us-gaap", {
        "Revenues": [dict(r, val=100) for r in (current, prior)],
        "RevenueFromContractWithCustomerExcludingAssessedTax": [dict(r, val=10) for r in (current, prior)],
        "OperatingIncomeLoss": [current, prior],
    })
    payload["cik"] = 1234
    return sorted(_companyfacts_snapshots(payload, ticker), key=lambda r: r.financial_period_end)


@pytest.mark.parametrize("ticker", ["ALPHA", "RENAMED", "ZZZZ"])
def test_independent_oi_survives_revenue_ambiguity_with_comparison(ticker):
    prior, current = fixture(ticker)
    assert current.revenue is None and current.operating_margin is None
    assert field_errors(current, "latest_revenue_yoy")
    assert not field_errors(current, "latest_operating_income")
    assert _earnings_quarters([prior, current])[-1].financial_period_end == date(2026, 6, 30)
    proof = reported_comparison_quality(formal=current, comparison=prior, ticker=ticker, cutoff=date(2026, 9, 22))
    assert proof["status"] == "PASS"
    assert [c["metric"] for c in proof["comparative_observations"]] == ["operating_income"]
    relation = proof["comparative_observations"][0]
    assert relation["delta"] == 50 and relation["growth_pct"] is None
    assert field_errors(current, "latest_operating_margin")


@pytest.mark.parametrize("change", ["ticker", "period", "filing", "unit", "value", "receipt", "identity", "extra_error"])
def test_source_integrity_cannot_be_masked_by_independent_field(change):
    prior, current = fixture()
    if change == "ticker":
        current.ticker = "ANOTHER"
    elif change == "period":
        current.financial_period_end = date(2026, 3, 31)
    elif change == "filing":
        current.filing_date = date(2026, 8, 2)
    elif change == "unit":
        current.currency = "KRW"
    elif change == "value":
        current.operating_income = 31
    elif change == "receipt":
        current.source_filing_id = "another"
    elif change == "identity":
        records = json.loads(current.raw_financial_fields)
        next(r for r in records if r["field"] == "operating_income")["issuer_cik"] = 9999
        current.raw_financial_fields = json.dumps(records)
    else:
        current.financial_hard_errors = json.dumps(["sec_business_occurrence_conflict", "issuer_mismatch"])
    assert field_errors(current, "operating_income")
    proof = reported_comparison_quality(formal=current, comparison=prior, ticker="RENAMED", cutoff=date(2026, 9, 22))
    assert proof["status"] == "FAIL"


def test_absolute_only_is_not_direction_ready():
    _, current = fixture()
    assert reported_comparison_quality(formal=current, comparison=None, ticker=current.ticker,
                                      cutoff=date(2026, 9, 22))["status"] == "FAIL"


def test_comparison_requires_same_receipt_currency_semantic_and_duration():
    prior, current = fixture()
    prior.currency = "TWD"
    assert reported_comparison_quality(formal=current, comparison=prior, ticker=current.ticker,
                                      cutoff=date(2026, 9, 22))["status"] == "FAIL"


@pytest.mark.parametrize("tag", ["Revenues", "OperatingIncomeLoss"])
def test_same_concept_conflict_remains_hard_failure(tag):
    row = _companyfact_entry(100, fp="Q2", start="2026-04-01", end="2026-06-30", filed="2026-08-01")
    payload = _companyfacts_payload("us-gaap", {tag: [row, dict(row, val=101)]})
    payload["cik"] = 1234
    current = _companyfacts_snapshots(payload, "SYNTHETIC")[0]
    metric = "revenue" if tag == "Revenues" else "operating_income"
    assert getattr(current, metric) is None
    assert "sec_business_occurrence_conflict" in field_errors(current, metric)


def test_taxonomy_revenue_labels_do_not_prove_total_or_component_role():
    from app.services.sec_business_field_quality_service import SEMANTICS
    assert "TOTAL_REVENUE" not in SEMANTICS.values()
    assert "COMPONENT_REVENUE" not in SEMANTICS.values()
    _, current = fixture()
    assert current.revenue is None
