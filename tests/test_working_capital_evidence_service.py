from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import date
from decimal import Decimal

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    FactType,
    FinancialFact,
    Metric,
    PeriodIdentity,
    PeriodType,
)
from app.services.working_capital_evidence_service import (
    CONTRACT_VERSION,
    FreshnessState,
    OfficialFinancialOccurrence,
    RelationType,
    build_sec_working_capital_batch,
    canonicalize_occurrences,
    classify_freshness,
    derive_comparable_movement,
    derive_cross_growth_relation,
    extract_opendart_occurrences,
    fact_available_at,
    industry_applicability,
    select_aligned_flow_pair,
    select_latest_comparable_balance,
)


RAW_SHA = "a" * 64


def _occurrence(
    *,
    tag: str,
    value: str = "100",
    end: date = date(2026, 6, 30),
    start: date | None = None,
    fiscal_year: int = 2026,
    fiscal_period: str = "Q2",
    accession: str = "0001-26-000001",
    filed: date = date(2026, 8, 1),
    namespace: str = "us-gaap",
    currency: str | None = "USD",
    unit: str | None = "USD",
) -> OfficialFinancialOccurrence:
    return OfficialFinancialOccurrence(
        issuer_id="sec:0000000001",
        value=Decimal(value),
        currency=currency,
        unit=unit,
        period_start=start,
        period_end=end,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        source_provider="sec_edgar_companyfacts",
        source_document_id=accession,
        source_document_type="10-Q",
        filing_date=filed,
        namespace=namespace,
        tag=tag,
        raw_payload_sha256=RAW_SHA,
        entity_scope="issuer_level",
        statement_basis="issuer_reported",
        source_column="val",
    )


def _fact(
    metric: Metric,
    value: str,
    *,
    start: date,
    end: date,
    period_type: PeriodType,
    fiscal_year: int,
    fiscal_quarter: int,
    semantic: str,
    accession: str,
) -> FinancialFact:
    token = hashlib.sha256(
        f"{metric.value}|{start}|{end}|{semantic}|{accession}".encode()
    ).hexdigest()[:16]
    return FinancialFact(
        fact_id=f"fact:{token}",
        issuer_id="sec:0000000001",
        metric=metric,
        value=Decimal(value),
        currency="USD",
        unit="USD",
        period=PeriodIdentity(
            start=start,
            end=end,
            period_type=period_type,
            fiscal_year=fiscal_year,
            fiscal_quarter=fiscal_quarter,
        ),
        entity_scope="issuer_level",
        statement_basis="issuer_reported",
        reported_or_derived="reported",
        source_provider="sec_edgar_companyfacts",
        source_document_id=accession,
        filing_date=end,
        source_occurrence_id=f"occ:{token}",
        raw_payload_sha256=RAW_SHA,
        semantic_mapping=semantic,
        fact_type=FactType.REPORTED,
        source_available_at=end,
        balance_scope="total" if period_type == PeriodType.POINT_IN_TIME else None,
        net_gross_scope=(
            "net" if period_type == PeriodType.POINT_IN_TIME else None
        ),
    )


def test_inventory_total_maps_but_component_does_not() -> None:
    payload = {
        "cik": 1,
        "facts": {
            "us-gaap": {
                "InventoryNet": {
                    "units": {
                        "USD": [
                            {
                                "val": 120,
                                "end": "2026-06-30",
                                "filed": "2026-08-01",
                                "accn": "0001-26-000001",
                                "form": "10-Q",
                                "fy": 2026,
                                "fp": "Q2",
                            }
                        ]
                    }
                },
                "InventoryFinishedGoods": {
                    "units": {
                        "USD": [
                            {
                                "val": 30,
                                "end": "2026-06-30",
                                "filed": "2026-08-01",
                                "accn": "0001-26-000001",
                                "form": "10-Q",
                                "fy": 2026,
                                "fp": "Q2",
                            }
                        ]
                    }
                },
            }
        },
    }
    batch = build_sec_working_capital_batch(
        payload, raw_payload_sha256=RAW_SHA, as_of_date=date(2026, 8, 21)
    )

    assert len(batch.facts) == 1
    assert batch.facts[0].metric == Metric.INVENTORY
    assert batch.facts[0].value == Decimal(120)
    assert batch.facts[0].balance_scope == "total"


def test_trade_and_broad_ar_ap_remain_separate() -> None:
    occurrences = (
        _occurrence(tag="AccountsReceivableNetCurrent", value="80"),
        _occurrence(tag="AccountsPayableTradeCurrent", value="40"),
        _occurrence(tag="AccountsPayableAndAccruedLiabilitiesCurrent", value="70"),
    )
    batch = canonicalize_occurrences(occurrences, as_of_date=date(2026, 8, 21))

    assert {(item.metric, item.value) for item in batch.facts} == {
        (Metric.BROAD_AR, Decimal(80)),
        (Metric.TRADE_AP, Decimal(40)),
        (Metric.BROAD_AP, Decimal(70)),
    }


def test_missing_or_negative_balance_never_becomes_zero() -> None:
    batch = canonicalize_occurrences(
        (_occurrence(tag="InventoryNet", value="-1"),),
        as_of_date=date(2026, 8, 21),
    )

    assert not batch.facts
    assert batch.denials[0]["reason"] == "negative_balance_requires_source_review"


def test_currency_or_unit_missing_fails_closed() -> None:
    batch = canonicalize_occurrences(
        (_occurrence(tag="InventoryNet", currency=None, unit=None),),
        as_of_date=date(2026, 8, 21),
    )

    assert not batch.facts
    assert batch.denials[0]["reason"] == "currency_or_unit_missing"


def test_latest_restatement_value_is_selected_with_original_fiscal_context() -> None:
    original = _occurrence(
        tag="InventoryNet",
        value="100",
        fiscal_year=2025,
        fiscal_period="Q2",
        accession="0001-25-000001",
        filed=date(2025, 8, 1),
        end=date(2025, 6, 30),
    )
    restated = replace(
        original,
        value=Decimal("110"),
        fiscal_year=2026,
        source_document_id="0001-26-000010",
        filing_date=date(2026, 2, 1),
    )
    batch = canonicalize_occurrences(
        (original, restated), as_of_date=date(2026, 8, 21)
    )

    assert len(batch.facts) == 1
    assert batch.facts[0].value == Decimal(110)
    assert batch.facts[0].period.fiscal_year == 2025
    assert batch.facts[0].source_document_id == "0001-26-000010"


def test_same_document_conflict_is_blocked() -> None:
    occurrence = _occurrence(tag="InventoryNet")
    batch = canonicalize_occurrences(
        (occurrence, replace(occurrence, value=Decimal("101"))),
        as_of_date=date(2026, 8, 21),
    )

    assert not batch.facts
    assert batch.conflicts == 1


def test_prior_fy_end_republished_in_q1_is_not_a_q1_comparable() -> None:
    prior_fy_as_q1 = _occurrence(
        tag="AccountsReceivableNetCurrent",
        value="100",
        end=date(2023, 12, 31),
        fiscal_year=2024,
        fiscal_period="Q1",
        accession="q1-comparative",
        filed=date(2024, 5, 1),
    )
    authoritative_fy = replace(
        prior_fy_as_q1,
        fiscal_period="FY",
        source_document_id="annual-amendment",
        source_document_type="10-K/A",
        filing_date=date(2026, 3, 1),
        frame="CY2023Q4I",
    )
    current_q1 = _occurrence(
        tag="AccountsReceivableNetCurrent",
        value="110",
        end=date(2025, 3, 31),
        fiscal_year=2025,
        fiscal_period="Q1",
        accession="current-q1",
        filed=date(2025, 5, 1),
    )
    batch = canonicalize_occurrences(
        (prior_fy_as_q1, authoritative_fy, current_q1),
        as_of_date=date(2026, 8, 21),
    )
    selection = select_latest_comparable_balance(
        batch.facts, metrics=(Metric.BROAD_AR,)
    )

    assert selection.status == EligibilityStatus.PARTIAL
    assert selection.current is not None
    assert selection.prior is None


def test_prior_year_same_fiscal_quarter_is_comparable() -> None:
    current = _fact(
        Metric.INVENTORY,
        "120",
        start=date(2026, 6, 30),
        end=date(2026, 6, 30),
        period_type=PeriodType.POINT_IN_TIME,
        fiscal_year=2026,
        fiscal_quarter=2,
        semantic="us-gaap:InventoryNet",
        accession="current",
    )
    prior = _fact(
        Metric.INVENTORY,
        "100",
        start=date(2025, 6, 30),
        end=date(2025, 6, 30),
        period_type=PeriodType.POINT_IN_TIME,
        fiscal_year=2025,
        fiscal_quarter=2,
        semantic="us-gaap:InventoryNet",
        accession="prior",
    )
    selection = select_latest_comparable_balance(
        (prior, current), metrics=(Metric.INVENTORY,)
    )
    movement = derive_comparable_movement(selection)

    assert selection.status == EligibilityStatus.ELIGIBLE
    assert movement.absolute_delta == Decimal(20)
    assert movement.growth_pct == Decimal(20)
    assert movement.direction == RelationType.BALANCE_INCREASED


def test_quarter_end_vs_prior_fy_is_not_yoy() -> None:
    current = _fact(
        Metric.INVENTORY,
        "120",
        start=date(2026, 6, 30),
        end=date(2026, 6, 30),
        period_type=PeriodType.POINT_IN_TIME,
        fiscal_year=2026,
        fiscal_quarter=2,
        semantic="us-gaap:InventoryNet",
        accession="current",
    )
    prior_fy = _fact(
        Metric.INVENTORY,
        "100",
        start=date(2025, 12, 31),
        end=date(2025, 12, 31),
        period_type=PeriodType.POINT_IN_TIME,
        fiscal_year=2025,
        fiscal_quarter=4,
        semantic="us-gaap:InventoryNet",
        accession="prior",
    )
    selection = select_latest_comparable_balance(
        (prior_fy, current), metrics=(Metric.INVENTORY,)
    )

    assert selection.status == EligibilityStatus.PARTIAL
    assert selection.prior is None


def test_non_calendar_fiscal_quarter_uses_fiscal_identity() -> None:
    current = _fact(
        Metric.INVENTORY,
        "120",
        start=date(2026, 5, 28),
        end=date(2026, 5, 28),
        period_type=PeriodType.POINT_IN_TIME,
        fiscal_year=2026,
        fiscal_quarter=3,
        semantic="us-gaap:InventoryNet",
        accession="current",
    )
    prior = _fact(
        Metric.INVENTORY,
        "100",
        start=date(2025, 5, 29),
        end=date(2025, 5, 29),
        period_type=PeriodType.POINT_IN_TIME,
        fiscal_year=2025,
        fiscal_quarter=3,
        semantic="us-gaap:InventoryNet",
        accession="prior",
    )

    assert select_latest_comparable_balance(
        (prior, current), metrics=(Metric.INVENTORY,)
    ).status == EligibilityStatus.ELIGIBLE


def test_zero_prior_preserves_absolute_delta_but_suppresses_growth() -> None:
    current = _fact(
        Metric.BROAD_AR,
        "10",
        start=date(2026, 6, 30),
        end=date(2026, 6, 30),
        period_type=PeriodType.POINT_IN_TIME,
        fiscal_year=2026,
        fiscal_quarter=2,
        semantic="us-gaap:AccountsReceivableNetCurrent",
        accession="current",
    )
    prior = replace(
        current,
        fact_id="prior",
        value=Decimal(0),
        period=replace(current.period, start=date(2025, 6, 30), end=date(2025, 6, 30), fiscal_year=2025),
        source_document_id="prior",
    )
    movement = derive_comparable_movement(
        select_latest_comparable_balance(
            (prior, current), metrics=(Metric.BROAD_AR,)
        )
    )

    assert movement.status == EligibilityStatus.PARTIAL
    assert movement.absolute_delta == Decimal(10)
    assert movement.growth_pct is None


def test_ytd_revenue_alignment_creates_typed_relation() -> None:
    current_balance = _fact(
        Metric.BROAD_AR,
        "130",
        start=date(2026, 6, 30),
        end=date(2026, 6, 30),
        period_type=PeriodType.POINT_IN_TIME,
        fiscal_year=2026,
        fiscal_quarter=2,
        semantic="us-gaap:AccountsReceivableNetCurrent",
        accession="current",
    )
    prior_balance = replace(
        current_balance,
        fact_id="prior-balance",
        value=Decimal(100),
        period=replace(current_balance.period, start=date(2025, 6, 30), end=date(2025, 6, 30), fiscal_year=2025),
        source_document_id="prior",
    )
    current_revenue = _fact(
        Metric.REVENUE,
        "1200",
        start=date(2026, 1, 1),
        end=date(2026, 6, 30),
        period_type=PeriodType.YTD,
        fiscal_year=2026,
        fiscal_quarter=2,
        semantic="us-gaap:Revenues",
        accession="current",
    )
    prior_revenue = _fact(
        Metric.REVENUE,
        "1000",
        start=date(2025, 1, 1),
        end=date(2025, 6, 30),
        period_type=PeriodType.YTD,
        fiscal_year=2025,
        fiscal_quarter=2,
        semantic="us-gaap:Revenues",
        accession="prior",
    )
    facts = (current_balance, prior_balance, current_revenue, prior_revenue)
    balances = select_latest_comparable_balance(
        facts, metrics=(Metric.BROAD_AR,)
    )
    flows = select_aligned_flow_pair(facts, metric=Metric.REVENUE, balances=balances)
    relation = derive_cross_growth_relation(balances, flows)

    assert flows.status == EligibilityStatus.ELIGIBLE
    assert relation.status == EligibilityStatus.ELIGIBLE
    assert relation.relation_type == RelationType.AR_GROWTH_GT_REVENUE_GROWTH
    assert relation.percentage_point_difference == Decimal(10)
    assert len(relation.input_fact_ids) == 4
    assert relation.formula == "BALANCE_YOY_PCT_MINUS_FLOW_YOY_PCT"


def test_unrelated_ttm_or_source_version_does_not_align() -> None:
    current = _fact(
        Metric.INVENTORY,
        "120",
        start=date(2026, 6, 30),
        end=date(2026, 6, 30),
        period_type=PeriodType.POINT_IN_TIME,
        fiscal_year=2026,
        fiscal_quarter=2,
        semantic="us-gaap:InventoryNet",
        accession="current",
    )
    prior = replace(
        current,
        fact_id="prior",
        value=Decimal(100),
        period=replace(current.period, start=date(2025, 6, 30), end=date(2025, 6, 30), fiscal_year=2025),
        source_document_id="prior",
    )
    ttm = _fact(
        Metric.REVENUE,
        "2000",
        start=date(2025, 7, 1),
        end=date(2026, 6, 30),
        period_type=PeriodType.TTM,
        fiscal_year=2026,
        fiscal_quarter=2,
        semantic="us-gaap:Revenues",
        accession="different",
    )
    balances = select_latest_comparable_balance(
        (current, prior), metrics=(Metric.INVENTORY,)
    )

    assert select_aligned_flow_pair(
        (ttm,), metric=Metric.REVENUE, balances=balances
    ).status == EligibilityStatus.BLOCKED


def test_future_filing_and_provisional_lag_are_explicit() -> None:
    fact = _fact(
        Metric.INVENTORY,
        "100",
        start=date(2026, 3, 31),
        end=date(2026, 3, 31),
        period_type=PeriodType.POINT_IN_TIME,
        fiscal_year=2026,
        fiscal_quarter=1,
        semantic="us-gaap:InventoryNet",
        accession="q1",
    )
    fact = replace(fact, source_available_at=date(2026, 5, 1))

    assert not fact_available_at(fact, date(2026, 4, 30))
    assert classify_freshness(
        fact,
        latest_formal_balance_date=date(2026, 3, 31),
        latest_provisional_period_end=date(2026, 6, 30),
    ) == FreshnessState.FORMAL_LAGGING_PROVISIONAL


def test_opendart_cfs_and_ofs_are_not_mixed() -> None:
    row = {
        "rcept_no": "20260814000001",
        "reprt_code": "11012",
        "bsns_year": "2026",
        "fs_div": "CFS",
        "sj_div": "BS",
        "account_id": "ifrs-full_Inventories",
        "thstrm_amount": "1000",
        "currency": "KRW",
    }
    cfs = extract_opendart_occurrences(
        (row,),
        issuer_id="opendart:001",
        business_year=2026,
        report_code="11012",
        filing_date=date(2026, 8, 14),
        source_document_id="20260814000001",
        raw_payload_sha256=RAW_SHA,
        requested_basis="CFS",
    )
    ofs = extract_opendart_occurrences(
        ({**row, "fs_div": "OFS"},),
        issuer_id="opendart:001",
        business_year=2026,
        report_code="11012",
        filing_date=date(2026, 8, 14),
        source_document_id="20260814000001",
        raw_payload_sha256=RAW_SHA,
        requested_basis="OFS",
    )

    assert cfs[0].statement_basis == "consolidated"
    assert ofs[0].statement_basis == "separate"


def test_project_contract_asset_and_accrual_tags_are_not_trade_balances() -> None:
    payload = {
        "cik": 1,
        "facts": {
            "us-gaap": {
                "ContractWithCustomerAssetCurrent": {"units": {"USD": []}},
                "AccruedLiabilitiesCurrent": {"units": {"USD": []}},
            }
        },
    }

    assert not build_sec_working_capital_batch(
        payload, raw_payload_sha256=RAW_SHA, as_of_date=date(2026, 8, 21)
    ).facts


def test_industry_negative_controls_and_contract_version() -> None:
    assert CONTRACT_VERSION == "working-capital-evidence-v1"
    assert set(industry_applicability("insurance_reinsurance").values()) == {
        "NOT_APPLICABLE"
    }
    assert industry_applicability("memory_semiconductor")["inventory"] == "PRIMARY"
    assert industry_applicability("biotech")["ar_vs_revenue"] == "NOT_APPLICABLE"
