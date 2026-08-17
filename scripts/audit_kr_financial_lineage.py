from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
import hashlib
import json
import os
from pathlib import Path

from sqlmodel import Session, create_engine, select

from app.models.financial import FinancialSnapshot
from app.models.watchlist import WatchlistItem
from app.services.historical_valuation_service import financial_period_end
from app.services.kr_financial_lineage_service import (
    FINANCIAL_LINEAGE_VERSION,
    growth_lineage_compatible,
    select_field_source,
)


DIRECT_FIELDS = {
    "Revenue": ("revenue", "latest_revenue"),
    "Operating Income": ("operating_income", "latest_operating_income"),
    "Net Income": ("net_income", "latest_net_income"),
    "Operating Margin": ("operating_margin", "latest_operating_margin"),
    "EPS": ("diluted_eps", "latest_diluted_eps"),
    "TTM EPS": (None, None),
    "BVPS": (None, None),
    "Operating Cash Flow": ("operating_cash_flow", None),
    "CAPEX": ("capex", None),
    "FCF": ("fcf", None),
    "Inventory": ("inventory", None),
    "ROE": (None, None),
    "ROIC": (None, None),
}

GROWTH_FIELDS = {
    "QoQ Revenue": ("revenue", "latest_revenue_qoq", "qoq"),
    "QoQ Operating Income": (
        "operating_income",
        "latest_operating_income_qoq",
        "qoq",
    ),
    "YoY Revenue": ("revenue", "latest_revenue_yoy", "yoy"),
    "YoY Operating Income": (
        "operating_income",
        "latest_operating_income_yoy",
        "yoy",
    ),
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only active-KR financial lineage coverage audit"
    )
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _period_rows(
    rows: list[FinancialSnapshot], period_end: date | None
) -> list[FinancialSnapshot]:
    return [row for row in rows if financial_period_end(row) == period_end]


def _legacy_basis(row: FinancialSnapshot | None) -> str:
    if row is None:
        return "unknown"
    return {
        "CFS": "verified_consolidated",
        "OFS": "verified_separate",
    }.get(str(row.fs_div or "").upper(), "unknown")


def _direct_cell(
    rows: list[FinancialSnapshot],
    *,
    attribute: str | None,
    lineage_field: str | None,
) -> dict[str, object]:
    period_end = max((financial_period_end(row) or date.min for row in rows), default=date.min)
    current_rows = _period_rows(rows, period_end if period_end != date.min else None)
    source_rows = [
        row for row in current_rows if attribute and getattr(row, attribute) is not None
    ]
    selected = select_field_source(current_rows, lineage_field) if lineage_field else None
    if selected is not None:
        row, lineage = selected
        return {
            "source_available": True,
            "statement_basis": lineage.get("statement_basis_state"),
            "amount_period": lineage.get("amount_period_type"),
            "comparison_period": None,
            "currency": lineage.get("currency"),
            "quality_state": lineage.get("quality_state"),
            "user_visible": lineage.get("lineage_verified") is True,
            "suppressed_reason": lineage.get("denial_reason"),
            "source_filing": lineage.get("source_filing"),
            "source_row_identity": lineage.get("source_row_identity"),
            "snapshot_type": row.snapshot_type,
        }
    source = max(
        source_rows,
        key=lambda row: (row.filing_date or row.reported_date or date.min, row.id or 0),
        default=None,
    )
    return {
        "source_available": bool(source_rows),
        "statement_basis": _legacy_basis(source),
        "amount_period": None,
        "comparison_period": None,
        "currency": source.currency if source else None,
        "quality_state": "unknown" if source_rows else "unavailable",
        "user_visible": False,
        "suppressed_reason": (
            "field_level_lineage_missing" if source_rows else "source_unavailable"
        ),
        "source_filing": source.source_filing_id if source else None,
        "source_row_identity": None,
        "snapshot_type": source.snapshot_type if source else None,
    }


def _growth_cell(
    rows: list[FinancialSnapshot],
    *,
    attribute: str,
    lineage_field: str,
    comparison: str,
) -> dict[str, object]:
    periods = sorted(
        {financial_period_end(row) for row in rows if financial_period_end(row)},
        reverse=True,
    )
    if not periods:
        return _direct_cell(rows, attribute=None, lineage_field=None)
    current_period = periods[0]
    expected = range(60, 121) if comparison == "qoq" else range(330, 401)
    comparison_period = next(
        (
            period
            for period in periods[1:]
            if (current_period - period).days in expected
        ),
        None,
    )
    current_rows = _period_rows(rows, current_period)
    comparison_rows = _period_rows(rows, comparison_period)
    current = select_field_source(current_rows, lineage_field)
    previous = select_field_source(comparison_rows, lineage_field)
    values_available = bool(
        any(getattr(row, attribute) is not None for row in current_rows)
        and any(getattr(row, attribute) is not None for row in comparison_rows)
    )
    compatible = bool(
        current
        and previous
        and growth_lineage_compatible(
            current[1], previous[1], comparison_type=comparison
        )
    )
    return {
        "source_available": values_available,
        "statement_basis": (
            current[1].get("statement_basis_state") if current else "unknown"
        ),
        "amount_period": (
            current[1].get("amount_period_type") if current else None
        ),
        "comparison_period": comparison_period.isoformat() if comparison_period else None,
        "currency": current[1].get("currency") if current else None,
        "quality_state": "verified_usable" if compatible else "unknown",
        "user_visible": compatible,
        "suppressed_reason": (
            None if compatible else "current_comparison_lineage_not_comparable"
            if values_available
            else "source_unavailable"
        ),
        "source_filing": current[1].get("source_filing") if current else None,
        "source_row_identity": (
            current[1].get("source_row_identity") if current else None
        ),
        "snapshot_type": current[0].snapshot_type if current else None,
    }


def build_audit(database: Path) -> dict[str, object]:
    url = f"sqlite:///file:{database.resolve()}?mode=ro&immutable=1&uri=true"
    engine = create_engine(url)
    with Session(engine) as session:
        watchlist = list(
            session.exec(select(WatchlistItem).where(WatchlistItem.active.is_(True))).all()
        )
        tickers = sorted(
            item.ticker
            for item in watchlist
            if item.ticker.isdigit() and len(item.ticker) == 6
        )
        snapshots = list(
            session.exec(
                select(FinancialSnapshot).where(FinancialSnapshot.ticker.in_(tickers))
            ).all()
        )
    grouped: dict[str, list[FinancialSnapshot]] = defaultdict(list)
    for snapshot in snapshots:
        grouped[snapshot.ticker].append(snapshot)
    matrix: dict[str, dict[str, object]] = {}
    for ticker in tickers:
        rows = grouped[ticker]
        fields = {
            label: _direct_cell(
                rows,
                attribute=attribute,
                lineage_field=lineage_field,
            )
            for label, (attribute, lineage_field) in DIRECT_FIELDS.items()
        }
        fields.update(
            {
                label: _growth_cell(
                    rows,
                    attribute=attribute,
                    lineage_field=lineage_field,
                    comparison=comparison,
                )
                for label, (attribute, lineage_field, comparison) in GROWTH_FIELDS.items()
            }
        )
        for cell in fields.values():
            cell.update(
                {
                    "before_persisted_source_available": cell["source_available"],
                    "before_suppression_status": "not_replayed",
                    "after_v2_prose_eligible": cell["user_visible"],
                    "after_v2_suppressed": not cell["user_visible"],
                    "after_v2_suppression_reason": cell["suppressed_reason"],
                }
            )
        matrix[ticker] = {
            "latest_period": max(
                (financial_period_end(row) or date.min for row in rows),
                default=date.min,
            ).isoformat(),
            "fields": fields,
        }
    cells = [cell for item in matrix.values() for cell in item["fields"].values()]
    return {
        "contract": FINANCIAL_LINEAGE_VERSION,
        "source_database_sha256": _sha256(database),
        "read_only": True,
        "active_tickers": tickers,
        "matrix": matrix,
        "summary": {
            "cells": len(cells),
            "source_available": sum(cell["source_available"] is True for cell in cells),
            "verified_user_visible": sum(cell["user_visible"] is True for cell in cells),
            "suppressed": sum(cell["user_visible"] is False for cell in cells),
            "historical_v2_rows": sum(
                FINANCIAL_LINEAGE_VERSION in (row.raw_financial_fields or "")
                for row in snapshots
            ),
        },
        "notes": [
            "The immutable operating copy predates financial-lineage-v2.",
            "Unknown historical fs_div is not reconstructed without the original authoritative row.",
            "Before suppression is not replayed; availability means a persisted source value existed.",
            "The matrix is coverage evidence, not a backfill or production mutation.",
        ],
    }


def main() -> None:
    args = _parser().parse_args()
    output = build_audit(args.database)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, args.output)


if __name__ == "__main__":
    main()
