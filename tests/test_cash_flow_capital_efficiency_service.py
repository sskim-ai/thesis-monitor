from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.cash_flow_capital_efficiency_service import (
    CapexScope,
    EligibilityStatus,
    FinancialFact,
    Metric,
    PeriodIdentity,
    PeriodType,
    derive_balance_delta,
    derive_ccc,
    derive_fcf,
    derive_qtd_from_ytd,
    derive_ratio,
    derive_standard_roic,
    derive_ttm,
    derive_working_capital_days,
    normalize_capex_cash_outflow,
    q1_ytd_as_qtd,
)
from scripts.phase9_0a_evidence import (
    _latest_pair,
    _occurrences,
    _sec_record,
    _taxonomy,
)


def _period(
    period_type: PeriodType = PeriodType.YTD,
    *,
    start: date = date(2026, 1, 1),
    end: date = date(2026, 6, 30),
    fiscal_year: int = 2026,
    fiscal_quarter: int | None = 2,
) -> PeriodIdentity:
    return PeriodIdentity(
        start=start,
        end=end,
        period_type=period_type,
        fiscal_year=fiscal_year,
        fiscal_quarter=fiscal_quarter,
    )


def _fact(
    metric: Metric,
    value: str,
    *,
    fact_id: str | None = None,
    period: PeriodIdentity | None = None,
    issuer_id: str = "issuer-1",
    currency: str = "KRW",
    unit: str = "KRW",
    entity_scope: str = "consolidated_issuer",
    statement_basis: str = "CFS",
    source_provider: str = "official_fixture",
    semantic_mapping: str | None = None,
    capex_scope: CapexScope | None = None,
    source_sign: str | None = None,
    restatement_policy_id: str | None = "latest_authoritative_v1",
) -> FinancialFact:
    resolved_period = period or _period()
    resolved_id = fact_id or f"fact:{metric.value}:{resolved_period.end}"
    return FinancialFact(
        fact_id=resolved_id,
        issuer_id=issuer_id,
        metric=metric,
        value=Decimal(value),
        currency=currency,
        unit=unit,
        period=resolved_period,
        entity_scope=entity_scope,
        statement_basis=statement_basis,
        reported_or_derived="reported",
        source_provider=source_provider,
        source_document_id="filing-1",
        filing_date=date(2026, 8, 14),
        source_occurrence_id=resolved_id,
        raw_payload_sha256="a" * 64,
        semantic_mapping=semantic_mapping or metric.value,
        source_reported_value=Decimal(value),
        source_sign=source_sign,
        capex_scope=capex_scope,
        restatement_policy_id=restatement_policy_id,
        as_of_date=date(2026, 8, 20),
    )


def _point(
    metric: Metric,
    value: str,
    point: date,
    *,
    semantic_mapping: str | None = None,
) -> FinancialFact:
    return _fact(
        metric,
        value,
        fact_id=f"fact:{metric.value}:{point}",
        period=_period(
            PeriodType.POINT_IN_TIME,
            start=point,
            end=point,
            fiscal_quarter=None,
        ),
        semantic_mapping=semantic_mapping,
    )


def test_period_identity_keeps_point_in_time_distinct_from_flow() -> None:
    with pytest.raises(ValueError, match="point_in_time_requires_one_date"):
        _period(PeriodType.POINT_IN_TIME)


def test_q1_verified_ytd_can_be_represented_as_qtd() -> None:
    q1 = _fact(
        Metric.OCF,
        "120",
        period=_period(
            start=date(2026, 1, 1),
            end=date(2026, 3, 31),
            fiscal_quarter=1,
        ),
    )

    decision = q1_ytd_as_qtd(q1)

    assert decision.status == EligibilityStatus.ELIGIBLE
    assert decision.fact is not None
    assert decision.fact.period.period_type == PeriodType.QTD
    assert decision.fact.input_fact_ids == (q1.fact_id,)


def test_h1_ytd_is_not_silently_treated_as_qtd() -> None:
    decision = q1_ytd_as_qtd(_fact(Metric.OCF, "220"))

    assert decision.status == EligibilityStatus.BLOCKED
    assert decision.reasons == ("q1_ytd_required",)


def test_q2_qtd_uses_compatible_adjacent_ytd_occurrences() -> None:
    q1 = _fact(
        Metric.OCF,
        "100",
        fact_id="ocf-q1-ytd",
        period=_period(
            start=date(2026, 1, 1),
            end=date(2026, 3, 31),
            fiscal_quarter=1,
        ),
    )
    h1 = _fact(Metric.OCF, "250", fact_id="ocf-h1-ytd")

    decision = derive_qtd_from_ytd(h1, q1)

    assert decision.status == EligibilityStatus.ELIGIBLE
    assert decision.fact is not None
    assert decision.fact.value == Decimal("150")
    assert decision.fact.period == _period(
        PeriodType.QTD,
        start=date(2026, 4, 1),
        end=date(2026, 6, 30),
        fiscal_quarter=2,
    )
    assert decision.fact.input_fact_ids == ("ocf-h1-ytd", "ocf-q1-ytd")


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("statement_basis", "OFS", "statement_basis_mismatch"),
        ("currency", "USD", "currency_mismatch"),
        ("restatement_policy_id", "old_version", "restatement_compatibility_unverified"),
    ],
)
def test_qtd_derivation_rejects_incompatible_lineage(
    field: str,
    value: str,
    reason: str,
) -> None:
    q1 = _fact(
        Metric.OCF,
        "100",
        fact_id="ocf-q1-ytd",
        period=_period(
            start=date(2026, 1, 1),
            end=date(2026, 3, 31),
            fiscal_quarter=1,
        ),
    )
    h1 = replace(_fact(Metric.OCF, "250", fact_id="ocf-h1-ytd"), **{field: value})

    decision = derive_qtd_from_ytd(h1, q1)

    assert decision.status == EligibilityStatus.BLOCKED
    assert reason in decision.reasons


def test_ttm_requires_fy_and_comparable_ytd_alignment() -> None:
    prior_fy = _fact(
        Metric.OCF,
        "500",
        fact_id="ocf-fy-2025",
        period=_period(
            PeriodType.FY,
            start=date(2025, 1, 1),
            end=date(2025, 12, 31),
            fiscal_year=2025,
            fiscal_quarter=4,
        ),
    )
    current_h1 = _fact(Metric.OCF, "300", fact_id="ocf-h1-2026")
    prior_h1 = _fact(
        Metric.OCF,
        "210",
        fact_id="ocf-h1-2025",
        period=_period(
            start=date(2025, 1, 1),
            end=date(2025, 6, 30),
            fiscal_year=2025,
        ),
    )

    decision = derive_ttm(prior_fy, current_h1, prior_h1)

    assert decision.status == EligibilityStatus.ELIGIBLE
    assert decision.fact is not None
    assert decision.fact.value == Decimal("590")
    assert decision.fact.period.period_type == PeriodType.TTM


def test_ttm_is_unavailable_without_comparable_prior_ytd() -> None:
    prior_fy = _fact(
        Metric.OCF,
        "500",
        period=_period(
            PeriodType.FY,
            start=date(2025, 1, 1),
            end=date(2025, 12, 31),
            fiscal_year=2025,
            fiscal_quarter=4,
        ),
    )
    current_h1 = _fact(Metric.OCF, "300")
    wrong_prior = _fact(
        Metric.OCF,
        "210",
        period=_period(
            start=date(2025, 1, 1),
            end=date(2025, 3, 31),
            fiscal_year=2025,
            fiscal_quarter=1,
        ),
    )

    decision = derive_ttm(prior_fy, current_h1, wrong_prior)

    assert decision.status == EligibilityStatus.BLOCKED
    assert "ytd_quarter_mismatch" in decision.reasons


def test_capex_negative_cash_flow_is_normalized_to_positive_magnitude() -> None:
    source = _fact(
        Metric.CAPEX,
        "-40",
        source_sign="negative_cash_outflow",
        capex_scope=CapexScope.PPE_ONLY,
    )

    decision = normalize_capex_cash_outflow(source, capex_scope=CapexScope.PPE_ONLY)

    assert decision.status == EligibilityStatus.ELIGIBLE
    assert decision.fact is not None
    assert decision.fact.value == Decimal("40")
    assert decision.fact.source_reported_value == Decimal("-40")


@pytest.mark.parametrize(
    "scope",
    [
        CapexScope.INTANGIBLES_ONLY,
        CapexScope.CAPITALIZED_SOFTWARE_ONLY,
        CapexScope.REPORTED_COMPANY_CAPEX,
    ],
)
def test_non_ppe_capex_is_preserved_but_not_promoted_to_baseline(scope: CapexScope) -> None:
    decision = normalize_capex_cash_outflow(
        _fact(Metric.CAPEX, "40", source_sign="positive_payment_magnitude"),
        capex_scope=scope,
    )

    assert decision.status == EligibilityStatus.PARTIAL
    assert decision.fact is None


def test_ambiguous_investing_outflow_is_not_capex() -> None:
    investing_total = _fact(Metric.OCF, "-90", semantic_mapping="net_investing_cash_flow")

    decision = normalize_capex_cash_outflow(
        investing_total,
        capex_scope=CapexScope.PPE_ONLY,
    )

    assert decision.status == EligibilityStatus.BLOCKED
    assert decision.reasons == ("metric_is_not_capex",)


def test_fcf_is_ocf_less_same_basis_ppe_capex() -> None:
    ocf = _fact(Metric.OCF, "200", fact_id="ocf")
    capex = _fact(
        Metric.CAPEX,
        "70",
        fact_id="capex",
        capex_scope=CapexScope.PPE_ONLY,
    )

    decision = derive_fcf(ocf, capex)

    assert decision.status == EligibilityStatus.ELIGIBLE
    assert decision.fact is not None
    assert decision.fact.value == Decimal("130")
    assert decision.fact.semantic_mapping == "backend_fcf_ppe_only"
    assert decision.fact.input_fact_ids == ("ocf", "capex")


def test_fcf_rejects_different_source_document_versions() -> None:
    ocf = _fact(Metric.OCF, "200", fact_id="ocf")
    capex = replace(
        _fact(
            Metric.CAPEX,
            "70",
            fact_id="capex",
            capex_scope=CapexScope.PPE_ONLY,
        ),
        source_document_id="different-filing",
    )

    decision = derive_fcf(ocf, capex)

    assert decision.status == EligibilityStatus.BLOCKED
    assert "source_document_mismatch" in decision.reasons


def test_fcf_rejects_quality_tainted_input() -> None:
    ocf = replace(_fact(Metric.OCF, "200", fact_id="ocf"), quality="CONFLICT")
    capex = _fact(
        Metric.CAPEX,
        "70",
        fact_id="capex",
        capex_scope=CapexScope.PPE_ONLY,
    )

    decision = derive_fcf(ocf, capex)

    assert decision.status == EligibilityStatus.BLOCKED
    assert "input_fact_quality_tainted" in decision.reasons


def test_fcf_rejects_cfs_ocf_plus_ofs_capex() -> None:
    ocf = _fact(Metric.OCF, "200", statement_basis="CFS")
    capex = _fact(
        Metric.CAPEX,
        "70",
        statement_basis="OFS",
        capex_scope=CapexScope.PPE_ONLY,
    )

    decision = derive_fcf(ocf, capex)

    assert decision.status == EligibilityStatus.BLOCKED
    assert "statement_basis_mismatch" in decision.reasons


def test_fcf_rejects_period_mismatch_and_non_ppe_scope() -> None:
    ocf = _fact(Metric.OCF, "200")
    capex = _fact(
        Metric.CAPEX,
        "70",
        period=_period(
            start=date(2026, 4, 1),
            end=date(2026, 6, 30),
            fiscal_quarter=2,
            period_type=PeriodType.QTD,
        ),
        capex_scope=CapexScope.PPE_PLUS_INTANGIBLES,
    )

    decision = derive_fcf(ocf, capex)

    assert decision.status == EligibilityStatus.BLOCKED
    assert "period_mismatch" in decision.reasons
    assert "baseline_fcf_requires_ppe_only_capex" in decision.reasons


def test_fcf_margin_rejects_mixed_periods() -> None:
    fcf = replace(_fact(Metric.FCF, "100"), reported_or_derived="derived")
    quarterly_revenue = _fact(
        Metric.REVENUE,
        "500",
        period=_period(
            PeriodType.QTD,
            start=date(2026, 4, 1),
            end=date(2026, 6, 30),
        ),
    )

    decision = derive_ratio(fcf, quarterly_revenue, metric=Metric.FCF_MARGIN)

    assert decision.status == EligibilityStatus.BLOCKED
    assert "period_mismatch" in decision.reasons


def test_working_capital_delta_requires_point_in_time_facts() -> None:
    current = _point(Metric.INVENTORY, "120", date(2026, 6, 30))
    prior = _point(Metric.INVENTORY, "90", date(2025, 6, 30))

    decision = derive_balance_delta(current, prior)

    assert decision.status == EligibilityStatus.ELIGIBLE
    assert decision.fact is not None
    assert decision.fact.value == Decimal("30")


def test_dso_requires_average_trade_receivables_not_total_receivables() -> None:
    revenue = _fact(Metric.REVENUE, "1000")
    beginning = _point(Metric.TOTAL_AR, "90", date(2025, 12, 31))
    ending = _point(Metric.TOTAL_AR, "110", date(2026, 6, 30))

    decision = derive_working_capital_days(
        revenue,
        beginning,
        ending,
        metric=Metric.DSO,
    )

    assert decision.status == EligibilityStatus.BLOCKED
    assert "balance_semantic_scope_mismatch" in decision.reasons


def test_dpo_requires_purchases_and_trade_payables() -> None:
    cogs = _fact(Metric.COGS, "700")
    beginning = _point(Metric.TRADE_AP, "80", date(2025, 12, 31))
    ending = _point(Metric.TRADE_AP, "100", date(2026, 6, 30))

    decision = derive_working_capital_days(
        cogs,
        beginning,
        ending,
        metric=Metric.DPO,
    )

    assert decision.status == EligibilityStatus.BLOCKED
    assert "flow_metric_mismatch" in decision.reasons


def test_ccc_requires_all_three_typed_components() -> None:
    period = _period()
    dso = _fact(Metric.DSO, "30", period=period, unit="days")
    inventory_days = _fact(Metric.INVENTORY_DAYS, "50", period=period, unit="days")
    dpo = _fact(Metric.DPO, "40", period=period, unit="days")

    complete = derive_ccc(dso, inventory_days, dpo)
    missing_component = derive_ccc(dso, inventory_days, inventory_days)

    assert complete.status == EligibilityStatus.ELIGIBLE
    assert complete.fact is not None
    assert complete.fact.value == Decimal("40")
    assert missing_component.status == EligibilityStatus.BLOCKED
    assert "all_ccc_components_required" in missing_component.reasons


def test_standard_roic_requires_explicit_excess_cash_policy() -> None:
    flow_period = _period(PeriodType.FY, end=date(2026, 12, 31), fiscal_quarter=4)
    operating_income = _fact(Metric.OPERATING_INCOME, "100", period=flow_period)
    pretax_income = _fact(Metric.PRETAX_INCOME, "80", period=flow_period)
    tax_expense = _fact(Metric.TAX_EXPENSE, "20", period=flow_period)
    beginning = date(2025, 12, 31)
    ending = date(2026, 12, 31)
    facts = (
        _point(Metric.EQUITY, "400", beginning),
        _point(Metric.EQUITY, "450", ending),
        _point(Metric.INTEREST_BEARING_DEBT, "150", beginning),
        _point(Metric.INTEREST_BEARING_DEBT, "140", ending),
        _point(Metric.EXCESS_CASH, "50", beginning),
        _point(Metric.EXCESS_CASH, "60", ending),
    )

    decision = derive_standard_roic(
        operating_income,
        pretax_income,
        tax_expense,
        *facts,
        industry_applicability="non_financial",
        excess_cash_policy_id=None,
    )

    assert decision.status == EligibilityStatus.BLOCKED
    assert "excess_cash_policy_unverified" in decision.reasons


def test_standard_roic_is_not_applicable_to_insurance() -> None:
    placeholder = _fact(Metric.OPERATING_INCOME, "1")

    decision = derive_standard_roic(
        placeholder,
        placeholder,
        placeholder,
        placeholder,
        placeholder,
        placeholder,
        placeholder,
        placeholder,
        placeholder,
        industry_applicability="financial_industry_not_applicable",
        excess_cash_policy_id=None,
    )

    assert decision.status == EligibilityStatus.NOT_APPLICABLE


def test_standard_roic_can_be_derived_only_with_verified_policy_and_inputs() -> None:
    flow_period = _period(PeriodType.FY, end=date(2026, 12, 31), fiscal_quarter=4)
    operating_income = _fact(Metric.OPERATING_INCOME, "100", period=flow_period)
    pretax_income = _fact(Metric.PRETAX_INCOME, "80", period=flow_period)
    tax_expense = _fact(Metric.TAX_EXPENSE, "20", period=flow_period)
    beginning = date(2025, 12, 31)
    ending = date(2026, 12, 31)
    excess_mapping = "verified_excess_cash_policy:policy-1"

    decision = derive_standard_roic(
        operating_income,
        pretax_income,
        tax_expense,
        _point(Metric.EQUITY, "400", beginning),
        _point(Metric.EQUITY, "450", ending),
        _point(Metric.INTEREST_BEARING_DEBT, "150", beginning),
        _point(Metric.INTEREST_BEARING_DEBT, "140", ending),
        _point(
            Metric.EXCESS_CASH,
            "50",
            beginning,
            semantic_mapping=excess_mapping,
        ),
        _point(
            Metric.EXCESS_CASH,
            "60",
            ending,
            semantic_mapping=excess_mapping,
        ),
        industry_applicability="non_financial",
        excess_cash_policy_id="policy-1",
    )

    assert decision.status == EligibilityStatus.ELIGIBLE
    assert decision.fact is not None
    assert decision.fact.value == Decimal("75") / Decimal("515")
    assert len(decision.fact.input_fact_ids) == 9


def test_foreign_issuer_level_margin_does_not_require_adr_ratio() -> None:
    foreign_ocf = _fact(
        Metric.OCF,
        "200",
        issuer_id="foreign-issuer",
        currency="TWD",
        unit="TWD",
    )
    foreign_revenue = _fact(
        Metric.REVENUE,
        "1000",
        issuer_id="foreign-issuer",
        currency="TWD",
        unit="TWD",
    )

    decision = derive_ratio(foreign_ocf, foreign_revenue, metric=Metric.OCF_MARGIN)

    assert decision.status == EligibilityStatus.ELIGIBLE
    assert decision.fact is not None
    assert decision.fact.value == Decimal("0.2")


def test_cross_currency_security_level_arithmetic_is_blocked() -> None:
    krw_fcf = replace(_fact(Metric.FCF, "100", currency="KRW", unit="KRW"))
    usd_revenue_proxy = _fact(Metric.REVENUE, "500", currency="USD", unit="USD")

    decision = derive_ratio(krw_fcf, usd_revenue_proxy, metric=Metric.FCF_MARGIN)

    assert decision.status == EligibilityStatus.BLOCKED
    assert "currency_mismatch" in decision.reasons


def test_provisional_revenue_cannot_fabricate_fcf() -> None:
    provisional_revenue = _fact(
        Metric.REVENUE,
        "1000",
        source_provider="official_provisional_earnings",
    )
    capex = _fact(
        Metric.CAPEX,
        "100",
        capex_scope=CapexScope.PPE_ONLY,
    )

    decision = derive_fcf(provisional_revenue, capex)

    assert decision.status == EligibilityStatus.BLOCKED
    assert "ocf_metric_required" in decision.reasons


def test_sec_pair_requires_unique_values_for_same_occurrence() -> None:
    base = {
        "accession": "filing-1",
        "start": "2026-01-01",
        "end": "2026-06-30",
        "unit": "USD",
        "filed": "2026-08-01",
    }
    ocf = [
        {**base, "value": 100, "semantic": "us-gaap:OCF"},
        {**base, "value": 101, "semantic": "us-gaap:OCF"},
    ]
    capex = [{**base, "value": 40, "semantic": "us-gaap:CAPEX"}]

    assert _latest_pair(ocf, capex) is None


def test_sec_occurrence_inventory_excludes_non_formal_rows() -> None:
    payload = {
        "facts": {
            "us-gaap": {
                "InventoryNet": {
                    "units": {
                        "USD": [
                            {"val": 10, "end": "2026-06-30", "form": "10-Q"},
                            {"val": 11, "end": "2026-07-01", "form": "8-K"},
                        ]
                    }
                }
            }
        }
    }

    values = _occurrences(
        payload,
        {"us-gaap": ("InventoryNet",)},
    )

    assert len(values) == 1
    assert values[0]["value"] == 10


@pytest.mark.parametrize(
    ("validation_metrics", "industry"),
    [
        ("HBM NAND ASP CAPEX FCF", "memory_semiconductor"),
        ("billing MW HPC lease project financing", "hpc_data_center"),
        ("combined ratio capital adequacy", "insurance_reinsurance"),
        ("electrical equipment order conversion", "industrial_epc"),
    ],
)
def test_industry_taxonomy_uses_economic_driver_not_ticker(
    validation_metrics: str,
    industry: str,
) -> None:
    row = {
        "industry": "",
        "sector": "",
        "valuation_framework": "",
        "validation_metrics": validation_metrics,
    }

    assert _taxonomy(row)[0] == industry


def test_foreign_issuer_record_separates_issuer_metrics_from_security_metrics(
    tmp_path: Path,
) -> None:
    occurrence = {
        "val": 100,
        "start": "2025-01-01",
        "end": "2025-12-31",
        "filed": "2026-03-01",
        "accn": "foreign-filing-1",
        "form": "20-F",
        "fy": 2025,
        "fp": "FY",
    }
    capex = {**occurrence, "val": 40}
    revenue = {**occurrence, "val": 500}
    payload = {
        "facts": {
            "ifrs-full": {
                "CashFlowsFromUsedInOperatingActivities": {
                    "units": {"TWD": [occurrence]}
                },
                "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities": {
                    "units": {"TWD": [capex]}
                },
                "Revenue": {"units": {"TWD": [revenue]}},
            }
        }
    }
    source = tmp_path / "companyfacts.json"
    source.write_text("{}", encoding="utf-8")
    row = {
        "ticker": "FOREIGN",
        "company_name": "Foreign Issuer",
        "industry": "Semiconductors",
        "sector": "Technology",
        "valuation_framework": "foundry CAPEX FCF",
        "validation_metrics": "semiconductor",
        "issuer_type": "foreign_private_issuer",
        "security_type": "depositary_receipt",
    }

    record = _sec_record(row, payload, source)

    assert record["metrics"]["fcf"]["status"] == "ELIGIBLE"
    assert record["issuer_level_boundary"] == (
        "issuer_metrics_do_not_require_depositary_ratio"
    )
    assert "require_verified_security_fx_basis" in record["security_level_boundary"]
