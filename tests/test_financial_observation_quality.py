from copy import deepcopy
from datetime import date
import json

import pytest

from app.models.financial import FinancialSnapshot
from app.services.financial_observation_quality_service import build_reported_observation_quality
from app.services.financial_observation_quality_service import digest
from app.services.cross_market_decision_engine_service import _compact
from app.services.kr_financial_lineage_service import opendart_lineage_records
from scripts.m12dr_financial_source_authority import (
    build_source_authority, comparative_facts, issuer_projection_receipt, source_quality,
)
from scripts.m12dk_current_source_authority import freeze_current_source_binding


def snapshots():
    records = []
    for i, (metric, account, label, current, prior) in enumerate((
        ("revenue", "ifrs-full_Revenue", "매출액", 100_000_000, 80_000_000),
        ("operating_income", "dart_OperatingIncomeLoss", "영업이익", 76_000_000, 30_000_000),
        ("net_income", "ifrs-full_ProfitLoss", "당기순이익", 120_000_000, 20_000_000),
    )):
        raw = dict(rcept_no="20260814000001", reprt_code="11012", bsns_year="2026",
                   fs_div="CFS", sj_div="CIS", account_id=account, account_nm=label,
                   account_detail="-", ord=str(i + 1), currency="KRW",
                   thstrm_amount=str(current), frmtrm_q_amount=str(prior))
        records.extend(opendart_lineage_records(raw, logical_field=metric, report_code="11012",
                                               selected=True, requested_fs_div="CFS"))
    common = dict(ticker="FICTIVE", period="2026-Q2", period_type="Q2", fiscal_year=2026,
                  period_scope="single-quarter", financial_period_end=date(2026, 6, 30),
                  currency="KRW", unit_scale=1.0, fs_div="CFS", sj_div="CIS",
                  source="OpenDART", provider="opendart", revenue=100_000_000,
                  operating_income=76_000_000, net_income=120_000_000, operating_margin=76,
                  financial_soft_outliers=json.dumps([
                      "net_income_exceeds_revenue", "unusually_high_or_low_operating_margin"]))
    formal = FinancialSnapshot(**common, filing_date=date(2026, 8, 14),
                               source_filing_id="20260814000001", raw_financial_fields=json.dumps(records))
    raw = []
    for i, (label, value) in enumerate((("매출액", "100"), ("영업이익", "76"), ("당기순이익", "120"))):
        raw.append(dict(raw_label=label, raw_value=value, raw_unit="백만원", raw_period="single_quarter",
                        raw_column_header="당기실적 (2026년 2분기)", source_receipt_no="20260729000001",
                        row_index=i, column_index=2, table_id="table", parse_method="html_semantic_table",
                        selected_reporting_period_end="2026-06-30", reporting_period_source="current_header_quarter",
                        reporting_period_confidence="high", current_period_date_candidates=["2026-06-30"]))
    prelim = FinancialSnapshot(**common, snapshot_type="preliminary_earnings", filing_date=date(2026, 7, 29),
                               source_filing_id="20260729000001", raw_financial_fields=json.dumps(raw),
                               reporting_period_source="current_header_quarter", reporting_period_confidence="high",
                               revenue_basis="fs_div=CFS", operating_income_basis="fs_div=CFS")
    return formal, prelim


def evaluate(formal, prelim):
    return build_reported_observation_quality(formal=formal, preliminary=prelim, ticker="FICTIVE",
                                             cutoff=date(2026, 9, 21))


def mutate_lineage(row, metric, key, value, role="current"):
    rows = json.loads(row.raw_financial_fields)
    for item in rows:
        if item["logical_field"] == metric and item["amount_role"] == role:
            item[key] = value
    row.raw_financial_fields = json.dumps(rows)


def test_corroborated_extreme_is_caution_not_normal_or_recurring():
    formal, prelim = snapshots()
    before = deepcopy((formal.model_dump(), prelim.model_dump()))
    result = evaluate(formal, prelim)
    assert result["status"] == "PASS"
    assert result["fields"]["current.operating_income"]["classification"] == "CORROBORATED_EXTREME"
    assert result["fields"]["current.net_income"]["state"] == "caution_usable"
    assert result["fields"]["current.operating_margin"]["value"] == 76
    assert "unusually_high_or_low_operating_margin" in result["quality_reason_codes"]
    assert all(not f["valuation_or_recurring_profit_eligible"] for f in result["fields"].values()
               if "valuation_or_recurring_profit_eligible" in f)
    revenue = result["comparative_observations"][0]
    assert revenue["metric"] == "revenue" and revenue["delta"] == 20_000_000
    assert revenue["growth_pct"] == 25 and revenue["direction"] == "higher"
    assert before == (formal.model_dump(), prelim.model_dump())
    assert result == evaluate(formal, prelim)


@pytest.mark.parametrize(("key", "value"), [
    ("ticker", "OTHER"), ("currency", "USD"), ("unit_scale", 1000),
    ("source_filing_id", None), ("fs_div", None), ("provider", "unverified"),
    ("filing_date", date(2026, 10, 1)),
    ("financial_statement_basis_warning", True),
    ("financial_hard_errors", '["source_conflict"]'),
])
def test_hard_identity_failures_remain_denied(key, value):
    formal, prelim = snapshots()
    setattr(formal, key, value)
    result = evaluate(formal, prelim)
    assert result["status"] == "FAIL"
    assert not result["comparative_observations"]
    assert result["fields"]["current.revenue"]["state"] == "denied"


@pytest.mark.parametrize(("key", "value"), [
    ("amount_period_start", "2026-01-01"), ("amount_period_end", "2026-05-31"),
    ("source_row_identity", "forged"), ("source_filing", "20260814000002"),
    ("currency", "USD"), ("source_column", "thstrm_add_amount"),
    ("statement_basis_state", "unknown"), ("amount", 999),
])
def test_bad_revenue_dependency_cannot_produce_revenue_growth(key, value):
    formal, prelim = snapshots()
    mutate_lineage(formal, "revenue", key, value)
    result = evaluate(formal, prelim)
    assert not any(c["metric"] == "revenue" for c in result["comparative_observations"])
    assert result["fields"]["current.operating_margin"]["state"] == "denied"


def test_unrelated_net_income_anomaly_does_not_deny_revenue():
    formal, _ = snapshots()
    result = evaluate(formal, None)
    assert result["fields"]["current.revenue"]["state"] == "caution_usable"
    assert result["fields"]["current.operating_income"]["state"] == "denied"
    assert result["fields"]["current.net_income"]["state"] == "denied"
    assert [r["metric"] for r in result["comparative_observations"]] == ["revenue"]


def test_operating_lineage_failure_taints_margin_not_revenue():
    formal, prelim = snapshots()
    mutate_lineage(formal, "operating_income", "lineage_verified", False)
    result = evaluate(formal, prelim)
    assert result["fields"]["current.operating_margin"]["state"] == "denied"
    assert result["fields"]["current.revenue"]["state"] == "caution_usable"


@pytest.mark.parametrize(("key", "value"), [
    ("ticker", "OTHER"), ("currency", "USD"), ("unit_scale", None),
    ("fs_div", "OFS"), ("financial_period_end", date(2026, 3, 31)),
    ("period_scope", "cumulative"), ("source_filing_id", "20260814000001"),
    ("operating_income", 75_000_000),
])
def test_invalid_corroborator_cannot_rescue_extreme(key, value):
    formal, prelim = snapshots()
    setattr(prelim, key, value)
    assert evaluate(formal, prelim)["fields"]["current.operating_income"]["state"] == "denied"


def test_comparison_scope_mismatch_fails():
    formal, prelim = snapshots()
    mutate_lineage(formal, "revenue", "amount_period_type", "year_to_date_cumulative", "comparison")
    result = evaluate(formal, prelim)
    assert not any(c["metric"] == "revenue" for c in result["comparative_observations"])


def test_half_year_filing_envelope_does_not_overwrite_exact_quarter_column():
    formal, prelim = snapshots()
    formal.period_type = "H1"
    formal.period_scope = "half-year"
    formal.is_cumulative = True
    result = evaluate(formal, prelim)
    assert result["status"] == "PASS"
    assert result["fields"]["current.revenue"]["lineage"]["amount_period_start"] == "2026-04-01"


def test_formal_source_never_inherits_historical_preliminary_classification():
    formal, prelim = snapshots()
    prelim.financial_soft_outliers = '["preliminary_profitability_outlier"]'
    result = evaluate(formal, prelim)
    assert "preliminary_profitability_outlier" in result["historical_preliminary_reason_codes"]
    assert "preliminary_profitability_outlier" not in result["quality_reason_codes"]
    assert result["fields"]["current.operating_income"]["source_type"] == "formal"


def test_absolute_level_without_comparison_is_not_direction_ready():
    formal, prelim = snapshots()
    formal.raw_financial_fields = json.dumps([r for r in json.loads(formal.raw_financial_fields)
                                              if r["amount_role"] == "current"])
    result = evaluate(formal, prelim)
    assert result["fields"]["current.operating_income"]["state"] == "caution_usable"
    assert result["status"] == "FAIL"


def authority_inputs():
    formal, preliminary = snapshots()
    inputs = dict(ticker="FICTIVE", cutoff="2026-09-21", formal=formal.model_dump(mode="json"),
                  preliminary=preliminary.model_dump(mode="json"))
    bundle = {"source_inputs": inputs, "source_inputs_sha256": digest(inputs), "source_generation_id": "frozen"}
    facts = comparative_facts(source_quality(bundle), ticker="FICTIVE", issuer_id="DART:12345678")
    stock = {"ticker": "FICTIVE", "fact_catalog": facts}
    packet = {"stocks": [stock], "packet_id": "p", "market": "kr", "assessment_date": "2026-09-21"}
    rows = [dict(ref_id="canonical:" + f["fact_id"], source_ref="stock.fact_catalog." + f["fact_id"],
                 category="earnings", label="comparison", statement=_compact(f["fields"]), as_of=f["as_of_date"])
            for f in facts]
    ep = {"ticker": "FICTIVE", "evidence": rows}
    refs = [r["ref_id"] for r in rows]
    cat = dict(ticker="FICTIVE", all_evidence_refs=refs, core_evidence_refs=refs, timing_evidence_refs=[],
               valuation_evidence_refs=[], positive_quality_refs=[], material_disclosure_failure_refs=[],
               claim_refs=[], atomic_claims=[])
    return dict(ticker="FICTIVE", source_generation_id="frozen", source_packet=packet, evidence_packet=ep,
                catalog=cat, source_metadata=rows, quality_bundles={"FICTIVE": bundle},
                issuer_bindings={"FICTIVE": {"issuer_id": "DART:12345678"}},
                frozen_binding=freeze_current_source_binding(source_generation_id="frozen", source_packet=packet,
                                                            evidence_packet=ep))


def test_comparative_authority_does_not_grant_security_valuation():
    result = build_source_authority(**authority_inputs())
    records = result["authority"]["authority_records"]
    assert len(records) == 2
    for record in records:
        assert "OVERALL_DIRECTION" in record["allowed_uses"]
        assert "VALUATION" not in record["allowed_uses"]
        assert "PASS_A_VALUATION_TIER" not in record["allowed_uses"]
        assert "ENTRY" not in record["allowed_uses"]


def test_tampered_quality_source_cannot_self_attest():
    inputs = authority_inputs()
    inputs["quality_bundles"]["FICTIVE"]["source_inputs"]["formal"]["revenue"] = 1
    with pytest.raises(ValueError, match="digest_mismatch"):
        build_source_authority(**inputs)


def test_tampered_comparative_number_denied_even_with_new_packet_hash():
    inputs = authority_inputs()
    ref = "canonical:" + inputs["source_packet"]["stocks"][0]["fact_catalog"][0]["fact_id"]
    inputs["source_packet"]["stocks"][0]["fact_catalog"][0]["fields"]["delta"] = 1
    inputs["frozen_binding"] = freeze_current_source_binding(
        source_generation_id="frozen", source_packet=inputs["source_packet"], evidence_packet=inputs["evidence_packet"])
    result = build_source_authority(**inputs)
    receipt = next(r for r in result["family_receipts"] if r["ref_id"] == ref)
    record = next(r for r in result["authority"]["authority_records"] if r["ref_id"] == ref)
    assert receipt["errors"] == ["comparative_fact_frozen_derivation_mismatch"]
    assert "OVERALL_DIRECTION" not in record["allowed_uses"]


def test_missing_verified_underlying_identity_cannot_project():
    receipt = issuer_projection_receipt(security_stock={"ticker": "ADR_FICTIVE", "valuation": {}},
                                       underlying_ticker="FICTIVE", issuer_binding={}, cutoff="2026-09-21")
    assert receipt["status"] == "FAIL"
    with pytest.raises(ValueError, match="projection_unverified"):
        comparative_facts(evaluate(*snapshots()), ticker="ADR_FICTIVE", issuer_id="DART:12345678", projection=receipt)
