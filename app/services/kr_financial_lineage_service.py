from __future__ import annotations

import json
from calendar import monthrange
from datetime import date
from typing import Iterable, Mapping

from app.models.financial import FinancialSnapshot


FINANCIAL_LINEAGE_VERSION = "financial-lineage-v2"

_REPORT_PERIODS = {
    "11013": (3, "single_quarter"),
    "11012": (6, "single_quarter"),
    "11014": (9, "single_quarter"),
    "11011": (12, "annual"),
}

_FIELD_ALIASES = {
    "latest_revenue": "revenue",
    "latest_operating_income": "operating_income",
    "latest_net_income": "net_income",
    "latest_basic_eps": "basic_eps",
    "latest_diluted_eps": "diluted_eps",
    "latest_operating_margin": "operating_margin",
    "latest_revenue_qoq": "revenue",
    "latest_revenue_yoy": "revenue",
    "latest_operating_income_qoq": "operating_income",
    "latest_operating_income_yoy": "operating_income",
    "latest_total_equity": "equity",
}


def _number(value: object) -> float | None:
    text = str(value or "").replace(",", "").strip()
    if not text or text == "-":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _year(item: Mapping[str, object]) -> int | None:
    try:
        value = int(str(item.get("bsns_year") or ""))
    except ValueError:
        return None
    return value if 1900 <= value <= 2200 else None


def _bounds(
    *,
    year: int | None,
    report_code: str,
    statement_type: str,
    amount_role: str,
    amount_variant: str,
) -> tuple[str | None, date | None, date | None]:
    definition = _REPORT_PERIODS.get(report_code)
    if year is None or definition is None:
        return None, None, None
    month, report_scope = definition
    year_offset = {
        "current": 0,
        "comparison": -1,
        "older_comparison": -2,
    }.get(amount_role)
    if year_offset is None:
        return None, None, None
    period_year = year + year_offset
    period_end = date(period_year, month, monthrange(period_year, month)[1])
    if statement_type == "BS":
        return "point_in_time", period_end, period_end
    if amount_variant == "annual_or_point" and report_scope != "annual":
        return None, None, None
    if amount_variant == "cumulative":
        return (
            "full_year" if report_code == "11011" else "year_to_date_cumulative",
            date(period_year, 1, 1),
            period_end,
        )
    if report_scope == "annual":
        return "full_year", date(period_year, 1, 1), period_end
    start_month = month - 2
    return "single_quarter", date(period_year, start_month, 1), period_end


def opendart_field_lineage(
    item: Mapping[str, object],
    *,
    logical_field: str,
    report_code: str,
    source_column: str,
    selected: bool,
    requested_fs_div: str | None = None,
) -> dict[str, object]:
    """Preserve one OpenDART source-column occurrence without guessing its basis."""
    fs_div = str(item.get("fs_div") or "").upper()
    if fs_div not in {"CFS", "OFS"}:
        fs_div = ""
    requested = str(requested_fs_div or "").upper()
    request_matches = requested in {"CFS", "OFS"} and (not fs_div or fs_div == requested)
    effective_fs_div = fs_div or (requested if request_matches else "")
    statement_basis = {
        "CFS": "consolidated",
        "OFS": "separate",
    }.get(effective_fs_div)
    statement_basis_state = {
        "CFS": "verified_consolidated",
        "OFS": "verified_separate",
    }.get(effective_fs_div, "unknown")

    source_specs = {
        "thstrm_amount": ("current", "standalone"),
        "thstrm_add_amount": ("current", "cumulative"),
        "frmtrm_q_amount": ("comparison", "standalone"),
        "frmtrm_add_amount": ("comparison", "cumulative"),
        "frmtrm_amount": ("comparison", "annual_or_point"),
        "bfefrmtrm_amount": ("older_comparison", "annual_or_point"),
    }
    amount_role, amount_variant = source_specs.get(
        source_column, ("unknown", "unknown")
    )
    statement_type = str(item.get("sj_div") or "").upper()
    period_type, period_start, period_end = _bounds(
        year=_year(item),
        report_code=report_code,
        statement_type=statement_type,
        amount_role=amount_role,
        amount_variant=amount_variant,
    )
    amount = _number(item.get(source_column))
    currency = str(item.get("currency") or "").upper() or None
    source_identity = ":".join(
        (
            str(item.get("rcept_no") or "unknown"),
            str(item.get("reprt_code") or report_code or "unknown"),
            str(item.get("bsns_year") or "unknown"),
            effective_fs_div or "unknown",
            str(item.get("sj_div") or "unknown"),
            str(item.get("account_id") or "unknown"),
            str(item.get("account_nm") or "unknown"),
            str(item.get("account_detail") or "unknown"),
            str(item.get("ord") or "unknown"),
        )
    )
    source_identity = f"{source_identity}:{source_column}"
    verified = bool(
        amount is not None
        and statement_basis
        and statement_type in {"BS", "IS", "CIS", "CF", "SCE"}
        and item.get("rcept_no")
        and item.get("account_id")
        and period_type
        and period_start
        and period_end
        and currency == "KRW"
    )
    return {
        "contract": FINANCIAL_LINEAGE_VERSION,
        "logical_field": logical_field,
        "selected_for_canonical": selected,
        "source_provider": "opendart",
        "source_type": "formal",
        "source_filing": item.get("rcept_no"),
        "rcept_no": item.get("rcept_no"),
        "bsns_year": _year(item),
        "reprt_code": str(item.get("reprt_code") or report_code or "") or None,
        "statement_basis": statement_basis,
        "statement_basis_state": statement_basis_state,
        "statement_basis_source": (
            "source_row_fs_div" if fs_div else "requested_full_statement_scope"
            if request_matches
            else None
        ),
        "fs_div": effective_fs_div or None,
        "statement_type": statement_type or None,
        "sj_div": statement_type or None,
        "sj_nm": item.get("sj_nm"),
        "account_id": item.get("account_id"),
        "account_name": item.get("account_nm"),
        "account_detail": item.get("account_detail"),
        "source_row_ordinal": item.get("ord"),
        "amount_role": amount_role,
        "amount_variant": amount_variant,
        "source_column": source_column,
        "amount": amount,
        "amount_period_type": period_type,
        "amount_period_start": period_start.isoformat() if period_start else None,
        "amount_period_end": period_end.isoformat() if period_end else None,
        "currency": currency,
        "source_row_identity": source_identity,
        "source_labels": {
            key: item.get(key)
            for key in ("thstrm_nm", "frmtrm_nm", "frmtrm_q_nm")
            if item.get(key)
        },
        "lineage_verified": verified,
        "quality_state": "verified_usable" if verified else "unknown",
        "denial_reason": (
            None
            if verified
            else "unsupported_financial_currency"
            if currency and currency != "KRW"
            else "opendart_field_lineage_unverified"
        ),
    }


def opendart_lineage_records(
    item: Mapping[str, object],
    *,
    logical_field: str,
    report_code: str,
    selected: bool,
    requested_fs_div: str | None = None,
) -> list[dict[str, object]]:
    columns = (
        "thstrm_amount",
        "thstrm_add_amount",
        "frmtrm_q_amount",
        "frmtrm_add_amount",
        "frmtrm_amount",
        "bfefrmtrm_amount",
    )
    return [
        opendart_field_lineage(
            item,
            logical_field=logical_field,
            report_code=report_code,
            source_column=column,
            selected=selected and column == "thstrm_amount",
            requested_fs_div=requested_fs_div,
        )
        for column in columns
        if _number(item.get(column)) is not None
    ]


def stored_financial_lineage(row: FinancialSnapshot) -> list[dict[str, object]]:
    try:
        values = json.loads(row.raw_financial_fields or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(values, list):
        return []
    return [
        dict(item)
        for item in values
        if isinstance(item, dict) and item.get("contract") == FINANCIAL_LINEAGE_VERSION
    ]


def selected_field_lineage(
    row: FinancialSnapshot, field: str
) -> dict[str, object] | None:
    logical_field = _FIELD_ALIASES.get(field)
    if logical_field is None:
        return None
    if logical_field == "operating_margin":
        return _margin_lineage(row)
    matches = [
        item
        for item in stored_financial_lineage(row)
        if item.get("logical_field") == logical_field
        and item.get("amount_role") == "current"
        and item.get("selected_for_canonical") is True
    ]
    identities = {str(item.get("source_row_identity")) for item in matches}
    return matches[0] if len(matches) == 1 and len(identities) == 1 else None


def _margin_lineage(row: FinancialSnapshot) -> dict[str, object] | None:
    revenue = selected_field_lineage(row, "latest_revenue")
    operating = selected_field_lineage(row, "latest_operating_income")
    if revenue is None or operating is None:
        return None
    comparable = homogeneous_financial_lineage((revenue, operating))
    return {
        **operating,
        "logical_field": "operating_margin",
        "source_row_identity": (
            f"{revenue.get('source_row_identity')}+{operating.get('source_row_identity')}"
        ),
        "dependency_lineages": [revenue, operating],
        "lineage_verified": comparable,
        "quality_state": "verified_usable" if comparable else "unknown",
        "denial_reason": None if comparable else "margin_dependency_basis_mismatch",
    }


def homogeneous_financial_lineage(records: Iterable[Mapping[str, object]]) -> bool:
    values = list(records)
    if not values or not all(item.get("lineage_verified") is True for item in values):
        return False
    keys = (
        "statement_basis_state",
        "amount_period_type",
        "amount_period_start",
        "amount_period_end",
        "currency",
    )
    return all(len({str(item.get(key) or "") for item in values}) == 1 for key in keys)


def growth_lineage_compatible(
    current: Mapping[str, object],
    comparison: Mapping[str, object],
    *,
    comparison_type: str,
) -> bool:
    if not all(item.get("lineage_verified") is True for item in (current, comparison)):
        return False
    for key in (
        "statement_basis_state",
        "amount_period_type",
        "currency",
        "source_type",
    ):
        if current.get(key) != comparison.get(key):
            return False
    current_account = current.get("account_id") or current.get("account_identifier")
    comparison_account = comparison.get("account_id") or comparison.get(
        "account_identifier"
    )
    if not current_account or current_account != comparison_account:
        return False
    current_field = current.get("logical_field") or current.get("field")
    comparison_field = comparison.get("logical_field") or comparison.get("field")
    if current_field and comparison_field:
        normalized_current = str(current_field).removesuffix("_qoq").removesuffix("_yoy")
        normalized_comparison = str(comparison_field).removesuffix("_qoq").removesuffix("_yoy")
        if normalized_current != normalized_comparison:
            return False
    try:
        current_end = date.fromisoformat(str(current["amount_period_end"]))
        comparison_end = date.fromisoformat(str(comparison["amount_period_end"]))
        current_start = date.fromisoformat(str(current["amount_period_start"]))
        comparison_start = date.fromisoformat(str(comparison["amount_period_start"]))
    except (KeyError, ValueError):
        return False
    if (current_end - current_start).days != (comparison_end - comparison_start).days:
        return False
    distance = (current_end - comparison_end).days
    return 60 <= distance <= 120 if comparison_type == "qoq" else 330 <= distance <= 400


def select_field_source(
    rows: Iterable[FinancialSnapshot],
    field: str,
) -> tuple[FinancialSnapshot, dict[str, object]] | None:
    """Select the latest verified correction, preferring formal CFS over OFS/preliminary."""
    candidates: list[tuple[tuple[int, int, date, int], FinancialSnapshot, dict[str, object]]] = []
    for row in rows:
        lineage = selected_field_lineage(row, field)
        if lineage is None or lineage.get("lineage_verified") is not True:
            continue
        formal = row.snapshot_type == "full_statement"
        basis_rank = 2 if lineage.get("statement_basis_state") == "verified_consolidated" else 1
        filed = row.filing_date or row.reported_date or date.min
        candidates.append(
            ((2 if formal else 1, basis_rank, filed, row.id or 0), row, lineage)
        )
    if not candidates:
        return None
    _priority, row, lineage = max(candidates, key=lambda item: item[0])
    return row, lineage
