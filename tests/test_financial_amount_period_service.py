from __future__ import annotations

from datetime import date

import pytest

from app.models.financial import FinancialSnapshot
from app.services.financial_amount_period_service import (
    apply_comparison_period_metadata,
    comparison_periods_compatible,
    financial_amount_period_label,
    financial_amount_period_lineage,
    unique_financial_source_row,
)


def _row(**overrides: object) -> FinancialSnapshot:
    values: dict[str, object] = {
        "ticker": "005930",
        "period": "2026-06-30",
        "snapshot_type": "full_statement",
        "source_filing_id": "20260816000001",
        "period_type": "Q2",
        "fiscal_year": 2026,
        "period_scope": "half-year",
        "normalization_method": "cumulative_less_prior_cumulative",
        "financial_period_end": date(2026, 6, 30),
        "filing_date": date(2026, 8, 16),
        "provider": "opendart",
        "fs_div": "CFS",
        "sj_div": "CIS",
        "revenue": 171_000_000_000_000,
        "cumulative_revenue": 305_000_000_000_000,
        "operating_income": 89_400_000_000_000,
        "cumulative_operating_income": 146_700_000_000_000,
        "total_equity": 100_000_000_000_000,
        "revenue_basis": (
            "포괄손익계산서; fs_div=CFS; sj_div=CIS; "
            "account_id=ifrs-full_Revenue; thstrm_nm=제58기 반기; "
            "period_scope=half-year; amount_scope=standalone_or_balance; "
            "report_code=11012"
        ),
        "operating_income_basis": (
            "포괄손익계산서; fs_div=CFS; sj_div=CIS; "
            "account_id=dart_OperatingIncomeLoss; thstrm_nm=제58기 반기; "
            "period_scope=half-year; amount_scope=standalone_or_balance; "
            "report_code=11012"
        ),
        "balance_sheet_basis": (
            "재무상태표; fs_div=CFS; sj_div=BS; "
            "account_id=ifrs-full_Equity; thstrm_nm=2026-06-30; "
            "report_code=11012"
        ),
    }
    values.update(overrides)
    return FinancialSnapshot(**values)


def test_h1_filing_can_contain_q2_single_quarter_amount() -> None:
    lineage = financial_amount_period_lineage(_row(), "latest_operating_income")

    assert lineage["amount_period_type"] == "single_quarter"
    assert financial_amount_period_label(lineage) == "2026년 2분기"
    assert "상반기" not in str(financial_amount_period_label(lineage))


def test_h1_cumulative_amount_keeps_cumulative_label() -> None:
    row = _row(
        revenue=305_000_000_000_000,
        normalization_method="reported_current_period",
    )

    lineage = financial_amount_period_lineage(row, "latest_revenue")

    assert lineage["amount_period_type"] == "year_to_date_cumulative"
    assert financial_amount_period_label(lineage) == "2026년 상반기 누적"


def test_same_filing_can_have_distinct_amount_periods_by_field() -> None:
    quarter_row = _row()
    cumulative_row = _row(
        revenue=305_000_000_000_000,
        normalization_method="reported_current_period",
    )
    quarter = financial_amount_period_lineage(quarter_row, "latest_revenue")
    cumulative = financial_amount_period_lineage(
        cumulative_row, "latest_revenue"
    )

    assert quarter["source_filing_identifier"] == cumulative["source_filing_identifier"]
    assert quarter["amount_period_type"] == "single_quarter"
    assert cumulative["amount_period_type"] == "year_to_date_cumulative"


@pytest.mark.parametrize(
    ("period_type", "period_scope", "period_end", "expected"),
    [
        ("Q3", "single-quarter", date(2026, 9, 30), "2026년 3분기"),
        ("Q3", "ytd", date(2026, 9, 30), "2026년 9개월 누적"),
        ("FY", "annual", date(2026, 12, 31), "2026년 연간"),
    ],
)
def test_quarter_ytd_and_annual_labels(
    period_type: str,
    period_scope: str,
    period_end: date,
    expected: str,
) -> None:
    cumulative = 20.0
    row = _row(
        period_type=period_type,
        period_scope=period_scope,
        financial_period_end=period_end,
        revenue=10.0 if period_scope == "single-quarter" else cumulative,
        cumulative_revenue=cumulative,
        normalization_method=(
            "reported_single_quarter"
            if period_scope == "single-quarter"
            else "reported_current_period"
        ),
    )

    assert financial_amount_period_label(
        financial_amount_period_lineage(row, "latest_revenue")
    ) == expected


def test_balance_sheet_amount_is_point_in_time() -> None:
    lineage = financial_amount_period_lineage(_row(), "latest_total_equity")

    assert lineage["amount_period_type"] == "point_in_time"
    assert financial_amount_period_label(lineage) == "2026-06-30 기준"


@pytest.mark.parametrize(
    "overrides",
    [
        {"normalization_method": "normalization_unavailable"},
        {"normalization_method": "reported_current_period;cumulative_less_prior_cumulative"},
        {
            "fs_div": None,
            "sj_div": None,
            "operating_income_basis": (
                "미분류재무표; account_id=dart_OperatingIncomeLoss; "
                "thstrm_nm=제58기 반기; report_code=11012"
            ),
        },
    ],
)
def test_ambiguous_period_or_statement_basis_is_denied(
    overrides: dict[str, object],
) -> None:
    lineage = financial_amount_period_lineage(
        _row(**overrides), "latest_operating_income"
    )

    assert lineage["lineage_verified"] is False
    assert financial_amount_period_label(lineage) is None


def test_statement_type_does_not_infer_consolidated_or_separate_basis() -> None:
    row = _row(
        fs_div=None,
        sj_div="IS",
        operating_income_basis=(
            "미분류재무표; fs_div=unknown; sj_div=IS; "
            "account_id=dart_OperatingIncomeLoss; thstrm_nm=제58기 반기; "
            "report_code=11012"
        ),
    )

    lineage = financial_amount_period_lineage(row, "latest_operating_income")

    assert lineage["consolidated_separate_basis"] is None
    assert lineage["lineage_verified"] is False


@pytest.mark.parametrize(
    ("statement_name", "expected"),
    [
        ("연결포괄손익계산서", "consolidated"),
        ("포괄손익계산서", "separate"),
    ],
)
def test_explicit_source_row_statement_name_resolves_basis(
    statement_name: str,
    expected: str,
) -> None:
    row = _row(
        fs_div=None,
        sj_div="IS",
        operating_income_basis=(
            f"{statement_name}; fs_div=unknown; sj_div=IS; "
            "account_id=dart_OperatingIncomeLoss; thstrm_nm=제58기 반기; "
            "report_code=11012"
        ),
    )

    lineage = financial_amount_period_lineage(row, "latest_operating_income")

    assert lineage["consolidated_separate_basis"] == expected
    assert lineage["statement_basis_source"] == "source_row_statement_name"
    assert lineage["lineage_verified"] is True


def test_source_row_must_match_uniquely() -> None:
    row = _row()

    assert unique_financial_source_row([row], "latest_revenue") is row
    assert unique_financial_source_row([row, _row()], "latest_revenue") is None


def test_comparison_period_and_amount_type_must_match() -> None:
    current = financial_amount_period_lineage(_row(), "latest_revenue_yoy")
    previous = financial_amount_period_lineage(
        _row(
            fiscal_year=2025,
            financial_period_end=date(2025, 6, 30),
            period="2025-06-30",
        ),
        "latest_revenue_yoy",
    )
    wrong = dict(previous, amount_period_type="year_to_date_cumulative")

    assert comparison_periods_compatible([current, previous], comparison="yoy")
    assert not comparison_periods_compatible([current, wrong], comparison="yoy")


def test_comparison_period_metadata_records_exact_prior_bounds() -> None:
    current = financial_amount_period_lineage(_row(), "latest_revenue_yoy")
    previous = financial_amount_period_lineage(
        _row(
            fiscal_year=2025,
            financial_period_end=date(2025, 6, 30),
            period="2025-06-30",
        ),
        "latest_revenue_yoy",
    )

    assert apply_comparison_period_metadata(
        [current, previous], comparison="yoy"
    )
    assert current["comparison_type"] == "yoy"
    assert current["comparison_period_start"] == "2025-04-01"
    assert current["comparison_period_end"] == "2025-06-30"


def test_preliminary_source_row_has_deterministic_identity() -> None:
    row = _row(
        snapshot_type="preliminary_earnings",
        period_scope="single-quarter",
        normalization_method="reported_single_quarter",
        revenue_basis=(
            "잠정실적; fs_div=CFS; sj_div=IS; thstrm_nm=2026년 2분기; "
            "period_scope=single-quarter; amount_scope=standalone_or_balance; "
            "report_code=preliminary"
        ),
    )

    lineage = financial_amount_period_lineage(row, "latest_revenue")

    assert lineage["account_identifier"] == "preliminary:revenue"
    assert lineage["lineage_verified"] is True
    assert financial_amount_period_label(lineage) == "2026년 2분기"
