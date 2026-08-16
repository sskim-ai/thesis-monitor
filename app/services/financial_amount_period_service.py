from __future__ import annotations

import re
from datetime import date
from typing import Iterable

from app.models.financial import FinancialSnapshot


AMOUNT_PERIOD_CONTRACT = "financial-amount-period-v1"

_FINANCIAL_FIELDS = {
    "latest_revenue": ("revenue", "revenue_basis", "cumulative_revenue", "flow"),
    "latest_operating_income": (
        "operating_income",
        "operating_income_basis",
        "cumulative_operating_income",
        "flow",
    ),
    "latest_operating_margin": (
        "operating_income",
        "operating_income_basis",
        "cumulative_operating_income",
        "flow",
    ),
    "latest_revenue_qoq": (
        "revenue",
        "revenue_basis",
        "cumulative_revenue",
        "flow",
    ),
    "latest_revenue_yoy": (
        "revenue",
        "revenue_basis",
        "cumulative_revenue",
        "flow",
    ),
    "latest_operating_income_qoq": (
        "operating_income",
        "operating_income_basis",
        "cumulative_operating_income",
        "flow",
    ),
    "latest_operating_income_yoy": (
        "operating_income",
        "operating_income_basis",
        "cumulative_operating_income",
        "flow",
    ),
    "latest_total_equity": ("total_equity", "balance_sheet_basis", None, "point"),
}


def _basis_value(basis: str | None, key: str) -> str | None:
    if not basis:
        return None
    match = re.search(rf"(?:^|;\s*){re.escape(key)}=([^;)]*)", basis)
    value = match.group(1).strip() if match else ""
    return value or None


def _period_end(row: FinancialSnapshot) -> date | None:
    return row.financial_period_end or row.financials_as_of


def _quarter_number(row: FinancialSnapshot) -> int | None:
    normalized = str(row.period_type or "").upper()
    if normalized in {"Q1", "Q2", "Q3", "Q4"}:
        return int(normalized[-1])
    if normalized == "H1":
        return 2
    period_end = _period_end(row)
    if period_end and period_end.month in {3, 6, 9, 12}:
        return period_end.month // 3
    return None


def _single_quarter_bounds(row: FinancialSnapshot) -> tuple[date, date] | None:
    year = row.fiscal_year
    quarter = _quarter_number(row)
    period_end = _period_end(row)
    if year is None or quarter is None or period_end is None:
        return None
    start_month = (quarter - 1) * 3 + 1
    return date(year, start_month, 1), period_end


def _cumulative_bounds(row: FinancialSnapshot) -> tuple[date, date] | None:
    period_end = _period_end(row)
    year = row.fiscal_year
    if period_end is None or year is None:
        return None
    return date(year, 1, 1), period_end


def _statement_name(basis: str | None) -> str:
    return str(basis or "").split(";", maxsplit=1)[0].strip()


def _statement_basis(row: FinancialSnapshot, basis: str | None) -> str | None:
    fs_div = str(row.fs_div or _basis_value(basis, "fs_div") or "").upper()
    if fs_div == "CFS":
        return "consolidated"
    if fs_div == "OFS":
        return "separate"
    statement_name = _statement_name(basis)
    if statement_name.startswith("연결"):
        return "consolidated"
    if statement_name in {
        "손익계산서",
        "포괄손익계산서",
        "재무상태표",
        "현금흐름표",
        "자본변동표",
    }:
        return "separate"
    return None


def _statement_basis_source(row: FinancialSnapshot, basis: str | None) -> str | None:
    fs_div = str(row.fs_div or _basis_value(basis, "fs_div") or "").upper()
    if fs_div in {"CFS", "OFS"}:
        return "source_row_fs_div"
    if _statement_basis(row, basis) is not None:
        return "source_row_statement_name"
    return None


def _amount_period(
    row: FinancialSnapshot,
    value_field: str,
    cumulative_field: str | None,
    amount_nature: str,
) -> tuple[str | None, tuple[date, date] | None, str | None]:
    methods = {
        item.strip()
        for item in str(row.normalization_method or "").split(";")
        if item.strip()
    }
    value = getattr(row, value_field)
    cumulative = getattr(row, cumulative_field) if cumulative_field else None
    period_scope = str(row.period_scope or "").lower()
    period_type = str(row.period_type or "").upper()

    if value is None:
        return None, None, "amount_missing"
    if amount_nature == "point":
        period_end = _period_end(row)
        return (
            ("point_in_time", (period_end, period_end), None)
            if period_end is not None
            else (None, None, "point_in_time_period_unverified")
        )
    if period_scope == "single-quarter" and methods == {"reported_single_quarter"}:
        return "single_quarter", _single_quarter_bounds(row), None
    if methods == {"cumulative_less_prior_cumulative"}:
        return "single_quarter", _single_quarter_bounds(row), None
    if cumulative is not None and float(value) == float(cumulative):
        if period_type == "FY" or period_scope == "annual":
            return "full_year", _cumulative_bounds(row), None
        if period_type in {"Q2", "H1"} or period_scope == "half-year":
            return "year_to_date_cumulative", _cumulative_bounds(row), None
        if period_type == "Q3" or period_scope == "ytd":
            return "year_to_date_cumulative", _cumulative_bounds(row), None
    return None, None, "amount_period_unverified"


def financial_amount_period_lineage(
    row: FinancialSnapshot,
    field: str,
) -> dict[str, object]:
    mapping = _FINANCIAL_FIELDS.get(field)
    if mapping is None:
        return {
            "contract": AMOUNT_PERIOD_CONTRACT,
            "field": field,
            "lineage_verified": False,
            "lineage_verification_status": "unsupported_field",
            "denial_reason": "amount_period_field_not_supported",
        }
    value_field, basis_field, cumulative_field, amount_nature = mapping
    basis = getattr(row, basis_field)
    amount_period_type, bounds, denial_reason = _amount_period(
        row, value_field, cumulative_field, amount_nature
    )
    statement_basis = _statement_basis(row, basis)
    logical_account = "revenue" if value_field == "revenue" else value_field
    account_id = _basis_value(basis, "account_id")
    source_account_id = account_id or (
        f"preliminary:{logical_account}"
        if row.snapshot_type == "preliminary_earnings"
        and _basis_value(basis, "report_code") == "preliminary"
        else None
    )
    source_row_identity = (
        ":".join(
            (
                str(row.source_filing_id),
                str(row.provider),
                str(source_account_id),
                str(row.fs_div or _basis_value(basis, "fs_div") or "unknown"),
                str(row.sj_div or _basis_value(basis, "sj_div") or "unknown"),
                str(_basis_value(basis, "thstrm_nm") or row.period),
                value_field,
            )
        )
        if row.source_filing_id and source_account_id
        else None
    )
    verified = bool(
        amount_period_type
        and bounds
        and statement_basis
        and source_row_identity
        and row.provider
        and _period_end(row)
    )
    if not statement_basis:
        denial_reason = "consolidated_or_separate_basis_unverified"
    elif not source_row_identity:
        denial_reason = "source_row_identity_unverified"
    return {
        "contract": AMOUNT_PERIOD_CONTRACT,
        "field": field,
        "source_provider": row.provider,
        "source_document_type": row.snapshot_type,
        "source_filing_identifier": row.source_filing_id,
        "filing_date": str(row.filing_date or row.reported_date or "") or None,
        "reporting_period_end": str(_period_end(row) or "") or None,
        "account_identifier": source_account_id,
        "account_name": logical_account,
        "statement_type": str(row.sj_div or _basis_value(basis, "sj_div") or "")
        or None,
        "consolidated_separate_basis": statement_basis,
        "statement_basis_source": _statement_basis_source(row, basis),
        "amount_period_type": amount_period_type,
        "amount_period_start": str(bounds[0]) if bounds else None,
        "amount_period_end": str(bounds[1]) if bounds else None,
        "single_quarter_cumulative_flag": (
            "single_quarter"
            if amount_period_type == "single_quarter"
            else "cumulative"
            if amount_period_type in {"year_to_date_cumulative", "full_year"}
            else "unknown"
        ),
        "normalization_method": row.normalization_method,
        "source_row_identity": source_row_identity,
        "lineage_verified": verified,
        "lineage_verification_status": "verified" if verified else "unverified",
        "denial_reason": None if verified else denial_reason,
    }


def financial_amount_period_label(lineage: dict[str, object]) -> str | None:
    if (
        lineage.get("lineage_verified") is not True
        and lineage.get("lineage_verification_status") != "verified"
    ):
        return None
    end_text = str(lineage.get("amount_period_end") or "")
    if len(end_text) < 7:
        return None
    year = int(end_text[:4])
    amount_type = str(lineage.get("amount_period_type") or "")
    month = int(end_text[5:7])
    if amount_type == "single_quarter" and month in {3, 6, 9, 12}:
        return f"{year}년 {month // 3}분기"
    if amount_type == "year_to_date_cumulative":
        return (
            f"{year}년 상반기 누적"
            if month == 6
            else f"{year}년 9개월 누적"
            if month == 9
            else None
        )
    if amount_type == "full_year":
        return f"{year}년 연간"
    if amount_type == "point_in_time":
        return f"{end_text} 기준"
    return None


def unique_financial_source_row(
    rows: Iterable[FinancialSnapshot],
    field: str,
) -> FinancialSnapshot | None:
    candidates = list(rows)
    if len(candidates) != 1:
        return None
    lineage = financial_amount_period_lineage(candidates[0], field)
    return candidates[0] if lineage.get("source_row_identity") else None


def comparison_periods_compatible(
    records: Iterable[dict[str, object]],
    *,
    comparison: str,
) -> bool:
    values = list(records)
    if len(values) != 2 or not all(
        item.get("lineage_verified") is True for item in values
    ):
        return False
    if not all(item.get("amount_period_end") for item in values):
        return all(str(item.get("provider") or "") != "opendart" for item in values)
    current, previous = values
    if current.get("amount_period_type") != previous.get("amount_period_type"):
        return False
    current_end = date.fromisoformat(str(current["amount_period_end"]))
    previous_end = date.fromisoformat(str(previous["amount_period_end"]))
    days = (current_end - previous_end).days
    return 60 <= days <= 120 if comparison == "qoq" else 330 <= days <= 400


def apply_comparison_period_metadata(
    records: list[dict[str, object]],
    *,
    comparison: str,
) -> bool:
    """Attach the exact comparison period selected for a growth-rate lineage."""
    verified = comparison_periods_compatible(records, comparison=comparison)
    for item in records:
        item["comparison_period_verified"] = verified
    if len(records) == 2:
        current, previous = records
        current["comparison_type"] = comparison
        current["comparison_period_start"] = previous.get("amount_period_start")
        current["comparison_period_end"] = previous.get("amount_period_end")
    return verified
