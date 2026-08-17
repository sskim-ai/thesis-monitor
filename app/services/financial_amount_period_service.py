from __future__ import annotations

import re
from datetime import date
from typing import Iterable

from app.models.financial import FinancialSnapshot
from app.services.kr_financial_lineage_service import (
    FINANCIAL_LINEAGE_VERSION,
    growth_lineage_compatible,
    selected_field_lineage,
)


AMOUNT_PERIOD_CONTRACT = "financial-amount-period-v1"
STATEMENT_BASIS_CONTRACT = "financial-statement-basis-v1"

VERIFIED_CONSOLIDATED = "verified_consolidated"
VERIFIED_SEPARATE = "verified_separate"
STATEMENT_BASIS_CONFLICT = "conflict"
STATEMENT_BASIS_UNKNOWN = "unknown"

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


def financial_statement_basis_decision(
    row: FinancialSnapshot,
    basis: str | None,
) -> dict[str, object]:
    """Resolve consolidated/separate basis without promoting a statement type."""
    row_fs_div = str(row.fs_div or "").upper()
    embedded_fs_div = str(_basis_value(basis, "fs_div") or "").upper()
    explicit_values = {
        value for value in (row_fs_div, embedded_fs_div) if value in {"CFS", "OFS"}
    }
    statement_name = _statement_name(basis)
    name_basis = (
        "consolidated"
        if statement_name.startswith("연결")
        else "separate"
        if statement_name.startswith("별도")
        else None
    )
    fs_basis = (
        "consolidated"
        if explicit_values == {"CFS"}
        else "separate"
        if explicit_values == {"OFS"}
        else None
    )
    conflict = bool(
        len(explicit_values) > 1
        or (fs_basis is not None and name_basis is not None and fs_basis != name_basis)
    )
    if conflict:
        return {
            "contract": STATEMENT_BASIS_CONTRACT,
            "state": STATEMENT_BASIS_CONFLICT,
            "basis": None,
            "source": "conflicting_source_row_evidence",
            "denial_reason": "financial_statement_basis_conflict",
            "evidence": {
                "row_fs_div": row_fs_div or None,
                "embedded_fs_div": embedded_fs_div or None,
                "statement_name": statement_name or None,
            },
        }
    if fs_basis is not None:
        return {
            "contract": STATEMENT_BASIS_CONTRACT,
            "state": (
                VERIFIED_CONSOLIDATED
                if fs_basis == "consolidated"
                else VERIFIED_SEPARATE
            ),
            "basis": fs_basis,
            "source": "source_row_fs_div",
            "denial_reason": None,
            "evidence": {
                "row_fs_div": row_fs_div or None,
                "embedded_fs_div": embedded_fs_div or None,
                "statement_name": statement_name or None,
            },
        }
    # A statement title is authoritative only when it explicitly says 연결/별도
    # and is bound to an identified filing row. IS/CIS alone is not basis evidence.
    if name_basis is not None and row.source_filing_id:
        return {
            "contract": STATEMENT_BASIS_CONTRACT,
            "state": (
                VERIFIED_CONSOLIDATED
                if name_basis == "consolidated"
                else VERIFIED_SEPARATE
            ),
            "basis": name_basis,
            "source": "authoritative_statement_title",
            "denial_reason": None,
            "evidence": {
                "row_fs_div": row_fs_div or None,
                "embedded_fs_div": embedded_fs_div or None,
                "statement_name": statement_name or None,
            },
        }
    return {
        "contract": STATEMENT_BASIS_CONTRACT,
        "state": STATEMENT_BASIS_UNKNOWN,
        "basis": None,
        "source": None,
        "denial_reason": "consolidated_or_separate_basis_unverified",
        "evidence": {
            "row_fs_div": row_fs_div or None,
            "embedded_fs_div": embedded_fs_div or None,
            "statement_name": statement_name or None,
        },
    }


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
    field_lineage = selected_field_lineage(row, field)
    if field_lineage is not None:
        amount_value = getattr(row, value_field)
        source_amount = field_lineage.get("amount")
        amount_matches = bool(
            amount_value is not None
            and source_amount is not None
            and abs(float(amount_value) - float(source_amount))
            <= max(1.0, abs(float(amount_value)) * 1e-12)
        )
        dependencies = field_lineage.get("dependency_lineages")
        if field == "latest_operating_margin":
            amount_matches = bool(
                row.operating_margin is not None
                and isinstance(dependencies, list)
                and len(dependencies) == 2
            )
        verified = bool(field_lineage.get("lineage_verified") is True and amount_matches)
        denial_reason = (
            None
            if verified
            else str(
                field_lineage.get("denial_reason")
                or "source_row_amount_does_not_match_snapshot"
            )
        )
        return {
            "contract": AMOUNT_PERIOD_CONTRACT,
            "financial_lineage_contract": FINANCIAL_LINEAGE_VERSION,
            "field": field,
            "source_provider": field_lineage.get("source_provider") or row.provider,
            "source_document_type": row.snapshot_type,
            "source_filing_identifier": field_lineage.get("source_filing"),
            "filing_date": str(row.filing_date or row.reported_date or "") or None,
            "reporting_period_end": field_lineage.get("amount_period_end"),
            "account_identifier": field_lineage.get("account_id"),
            "account_name": field_lineage.get("account_name"),
            "statement_type": field_lineage.get("statement_type"),
            "statement_basis_contract": STATEMENT_BASIS_CONTRACT,
            "statement_basis_state": field_lineage.get("statement_basis_state"),
            "consolidated_separate_basis": field_lineage.get("statement_basis"),
            "statement_basis_source": field_lineage.get("statement_basis_source"),
            "statement_basis_evidence": {
                "fs_div": field_lineage.get("fs_div"),
                "sj_div": field_lineage.get("sj_div"),
                "source_column": field_lineage.get("source_column"),
            },
            "amount_period_type": field_lineage.get("amount_period_type"),
            "amount_period_start": field_lineage.get("amount_period_start"),
            "amount_period_end": field_lineage.get("amount_period_end"),
            "single_quarter_cumulative_flag": (
                "single_quarter"
                if field_lineage.get("amount_period_type") == "single_quarter"
                else "cumulative"
                if field_lineage.get("amount_period_type")
                in {"year_to_date_cumulative", "full_year"}
                else "unknown"
            ),
            "currency": field_lineage.get("currency"),
            "source_type": field_lineage.get("source_type"),
            "normalization_method": row.normalization_method,
            "source_row_identity": field_lineage.get("source_row_identity"),
            "dependency_lineages": dependencies or [],
            "lineage_verified": verified,
            "lineage_verification_status": "verified" if verified else "unverified",
            "denial_reason": denial_reason,
        }
    basis = getattr(row, basis_field)
    amount_period_type, bounds, denial_reason = _amount_period(
        row, value_field, cumulative_field, amount_nature
    )
    statement_decision = financial_statement_basis_decision(row, basis)
    statement_basis = statement_decision.get("basis")
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
        denial_reason = str(
            statement_decision.get("denial_reason")
            or "consolidated_or_separate_basis_unverified"
        )
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
        "statement_basis_contract": STATEMENT_BASIS_CONTRACT,
        "statement_basis_state": statement_decision.get("state"),
        "consolidated_separate_basis": statement_basis,
        "statement_basis_source": statement_decision.get("source"),
        "statement_basis_evidence": statement_decision.get("evidence"),
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
    basis_label = {
        VERIFIED_CONSOLIDATED: "연결 기준",
        VERIFIED_SEPARATE: "별도 기준",
    }.get(str(lineage.get("statement_basis_state") or ""))
    if basis_label is None:
        return None
    if amount_type == "single_quarter" and month in {3, 6, 9, 12}:
        return f"{year}년 {month // 3}분기 {basis_label}"
    if amount_type == "year_to_date_cumulative":
        period_label = (
            f"{year}년 상반기 누적"
            if month == 6
            else f"{year}년 9개월 누적"
            if month == 9
            else None
        )
        return f"{period_label} {basis_label}" if period_label else None
    if amount_type == "full_year":
        return f"{year}년 연간 {basis_label}"
    if amount_type == "point_in_time":
        return f"{end_text} {basis_label}"
    return None


def unique_financial_source_row(
    rows: Iterable[FinancialSnapshot],
    field: str,
) -> FinancialSnapshot | None:
    candidates = list(rows)
    mapping = _FINANCIAL_FIELDS.get(field)
    if mapping is None:
        return None
    basis_field = mapping[1]
    consolidated = [
        row
        for row in candidates
        if financial_statement_basis_decision(
            row,
            getattr(row, basis_field),
        ).get("state")
        == VERIFIED_CONSOLIDATED
    ]
    if len(consolidated) == 1:
        candidates = consolidated
    elif len(consolidated) > 1 or len(candidates) != 1:
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
    if current.get("financial_lineage_contract") == FINANCIAL_LINEAGE_VERSION or (
        previous.get("financial_lineage_contract") == FINANCIAL_LINEAGE_VERSION
    ):
        return growth_lineage_compatible(
            current,
            previous,
            comparison_type=comparison,
        )
    if current.get("amount_period_type") != previous.get("amount_period_type"):
        return False
    if current.get("statement_basis_state") != previous.get("statement_basis_state"):
        return False
    for key in ("account_identifier", "currency", "source_type"):
        current_value = current.get(key)
        previous_value = previous.get(key)
        if current_value or previous_value:
            if current_value != previous_value:
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
