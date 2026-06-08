from __future__ import annotations

import argparse
from datetime import date

from sqlmodel import Session, select

from app.database import init_db, engine
from app.models.financial import FinancialSnapshot


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _upsert_snapshot(args: argparse.Namespace) -> FinancialSnapshot:
    init_db()
    with Session(engine) as session:
        snapshot = session.exec(
            select(FinancialSnapshot).where(
                FinancialSnapshot.ticker == args.ticker.upper(),
                FinancialSnapshot.period == args.period,
                FinancialSnapshot.provider == args.provider,
            )
        ).first()
        if snapshot is None:
            snapshot = FinancialSnapshot(ticker=args.ticker.upper(), period=args.period)
            session.add(snapshot)

        snapshot.reported_date = _parse_date(args.reported_date)
        snapshot.source = args.source
        snapshot.provider = args.provider
        snapshot.fs_div = args.fs_div
        snapshot.sj_div = args.sj_div
        snapshot.revenue_basis = args.revenue_basis
        snapshot.operating_income_basis = args.operating_income_basis
        snapshot.balance_sheet_basis = args.balance_sheet_basis
        snapshot.quality_warnings = args.quality_warnings
        snapshot.revenue = args.revenue
        snapshot.operating_income = args.operating_income
        snapshot.net_income = args.net_income
        snapshot.operating_margin = (
            args.operating_income / args.revenue * 100 if args.revenue else None
        )
        snapshot.guidance = args.guidance
        session.commit()
        session.refresh(snapshot)
        return snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed one FinancialSnapshot row for local comparison testing."
    )
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--period", required=True)
    parser.add_argument("--reported-date", required=True)
    parser.add_argument("--provider", default="opendart")
    parser.add_argument("--source", default="manual_seed")
    parser.add_argument("--fs-div", default="CFS")
    parser.add_argument("--sj-div", default="IS")
    parser.add_argument("--revenue", type=float, required=True)
    parser.add_argument("--operating-income", type=float, required=True)
    parser.add_argument("--net-income", type=float, default=None)
    parser.add_argument("--revenue-basis", default="manual seed; fs_div=CFS; sj_div=IS")
    parser.add_argument("--operating-income-basis", default="manual seed; fs_div=CFS; sj_div=IS")
    parser.add_argument("--balance-sheet-basis", default=None)
    parser.add_argument("--quality-warnings", default=None)
    parser.add_argument("--guidance", default="manual seed snapshot")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    snapshot = _upsert_snapshot(args)
    print(
        "seeded snapshot:",
        snapshot.ticker,
        snapshot.period,
        snapshot.reported_date,
        snapshot.revenue,
        snapshot.operating_income,
        snapshot.operating_margin,
    )


if __name__ == "__main__":
    main()
