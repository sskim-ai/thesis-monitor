"""R19 API column semantics, not source fiscal dates or native-use authority."""
from copy import deepcopy

import pytest

from scripts import opendart_revenue_pilot as p
from test_opendart_revenue_pilot import company, filing, financial, raw


def test_unsupported_report_does_not_invent_three_month_duration():
    payload, report = financial(), filing()
    payload["list"][0]["reprt_code"] = report["reprt_code"] = "unsupported"
    parsed = p.parse_revenue(raw(payload), company(), report, "TEST_ONLY")
    assert parsed["amount_semantics"] == "UNKNOWN_PERIOD"
    assert parsed["current_period_start"] is None
    assert parsed["current_period_end"] is None
    assert parsed["canonical_value"] is None


@pytest.mark.parametrize("code", ["11013", "11012", "11014"])
@pytest.mark.parametrize("statement", ["IS", "CIS"])
def test_income_current_and_cumulative_columns_are_distinct(code, statement):
    assert p.amount_column_semantics(code, statement, "thstrm_amount") == "quarter_3_month"
    assert p.amount_column_semantics(code, statement, "thstrm_add_amount") == "year_to_date"
    payload, report = financial(), filing()
    payload["list"][0].update(reprt_code=code, sj_div=statement)
    report["reprt_code"] = code
    parsed = p.parse_revenue(raw(payload), company(), report, "TEST_ONLY")
    assert parsed["amount_field"] == "thstrm_amount"
    assert parsed["original_decimal_text"] == payload["list"][0]["thstrm_amount"]
    assert parsed["cumulative_amount_semantics"] == "year_to_date"
    assert parsed["amount_semantics_contract"] == "opendart-income-column-semantics-v1"
    assert parsed["unit_scale"] is None and parsed["canonical_value"] is None
    assert parsed["current_period_start"] is None and parsed["current_period_end"] is None
    assert parsed["source_status"] == "CAPTURED_UNQUALIFIED"
    assert parsed["core_permission"] == "NOT_ISSUED"


@pytest.mark.parametrize(
    "code,statement,field",
    [
        ("unsupported", "IS", "thstrm_amount"),
        ("11012", "BS", "thstrm_amount"),
        ("11012", "CF", "thstrm_amount"),
        ("11012", "SCE", "thstrm_add_amount"),
        ("11012", "unknown", "thstrm_amount"),
        ("11012", "IS", "invented"),
        ("11012", "IS", "frmtrm_amount"),
        ("11011", "IS", "thstrm_add_amount"),
        ("11011", "BS", "thstrm_amount"),
        (None, "IS", "thstrm_amount"),
    ],
)
def test_unsupported_column_contract_has_unknown_period(code, statement, field):
    assert p.amount_column_semantics(code, statement, field) == "UNKNOWN_PERIOD"


@pytest.mark.parametrize("statement", ["IS", "CIS"])
def test_annual_current_column_is_not_interim(statement):
    assert p.amount_column_semantics("11011", statement, "thstrm_amount") == "annual"


def test_cumulative_value_cannot_replace_missing_current_value():
    payload = financial()
    del payload["list"][0]["thstrm_amount"]
    with pytest.raises(p.PilotError, match="DECIMAL_TEXT_INVALID"):
        p.parse_revenue(raw(payload), company(), filing(), "TEST_ONLY")


def test_column_semantics_cannot_issue_core_permission():
    parsed = p.parse_revenue(raw(financial()), company(), filing(), "TEST_ONLY")
    forged = deepcopy(parsed)
    forged.update(unit_scale=1, current_period_start="2026-04-01",
                  current_period_end="2026-06-30", core_permission="ALLOWED")
    with pytest.raises(p.PilotError, match="NATIVE_CONSUMER_AUTHORITY_NOT_ISSUED"):
        p.deny_native_use(forged, consumer="core_current_fact")
