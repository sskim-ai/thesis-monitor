import argparse
import asyncio
import json
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.event import Event
from app.models.financial import DataBackfillState, FinancialSnapshot
from app.models.watchlist import WatchlistItem
from app.services.capital_action_service import CapitalActionService
from app.services.collection_service import CollectionService
from app.services.dividend_history_service import DividendHistoryService
from app.services.financial_backfill_service import backfill_financial_snapshots
from app.services.sec_financial_snapshot_service import SecFinancialSnapshotService


async def upgrade(years: int = 5) -> list[dict[str, object]]:
    init_db()
    collection = CollectionService()
    dividend = DividendHistoryService()
    capital_actions = CapitalActionService()
    sec = SecFinancialSnapshotService()
    results: list[dict[str, object]] = []
    with Session(engine) as session:
        items = list(
            session.exec(
                select(WatchlistItem).where(WatchlistItem.active.is_(True)).order_by(WatchlistItem.ticker)
            ).all()
        )
        for item in items:
            state = session.get(DataBackfillState, item.ticker) or DataBackfillState(ticker=item.ticker)
            state.backfill_status = "running"
            state.backfill_started_at = datetime.now(timezone.utc)
            state.backfill_years_requested = years
            session.add(state)
            session.commit()
            warnings: list[str] = []
            try:
                await collection.collect_events(session, item.ticker, 400)
                if (item.exchange or "").upper() == "KRX" or item.ticker.isdigit():
                    item.issuer_type = "krx"
                    result = await backfill_financial_snapshots(session, item.ticker, years=years)
                    warnings.extend(result.warnings)
                else:
                    forms = [
                        event for event in session.exec(select(Event).where(Event.ticker == item.ticker)).all()
                        if "filed 20-f" in event.title.lower() or "filed 6-k" in event.title.lower()
                    ]
                    item.issuer_type = "foreign_private_issuer" if forms else "domestic_us"
                    from app.config import get_settings

                    settings = get_settings()
                    if settings.sec_user_agent:
                        try:
                            await sec.refresh(session, item.ticker, settings.sec_user_agent)
                        except Exception as exc:  # noqa: BLE001
                            warnings.append(f"sec_financial_refresh:{type(exc).__name__}")
                events = list(session.exec(select(Event).where(Event.ticker == item.ticker)).all())
                for event in events:
                    dividend.ingest_event(session, event)
                    capital_actions.canonicalize(session, event)
                rows = list(
                    session.exec(
                        select(FinancialSnapshot)
                        .where(FinancialSnapshot.ticker == item.ticker)
                        .order_by(FinancialSnapshot.filing_date)
                    ).all()
                )
                dividend.sync_financial_snapshots(session, item.ticker, rows)
                dividend.sync_capital_returns(session, item.ticker, rows)
                dates = [
                    row.financial_period_end or row.financials_as_of
                    for row in rows
                    if row.financial_period_end or row.financials_as_of
                ]
                years_available = (
                    (max(dates) - min(dates)).days / 365.25 if len(dates) > 1 else 0.0
                )
                state.backfill_status = "complete"
                state.backfill_years_available = round(years_available, 2)
                state.backfill_gap_reason = (
                    None if years_available >= min(3, years) else "insufficient_provider_history"
                )
                results.append(
                    {
                        "ticker": item.ticker,
                        "issuer_type": item.issuer_type,
                        "financial_rows": len(rows),
                        "financial_history_years": round(years_available, 2),
                        "warning_count": len(warnings),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                state.backfill_status = "partial"
                state.backfill_gap_reason = type(exc).__name__
                warnings.append(type(exc).__name__)
                results.append(
                    {"ticker": item.ticker, "status": "partial", "warnings": warnings}
                )
            state.backfill_completed_at = datetime.now(timezone.utc)
            state.updated_at = datetime.now(timezone.utc)
            session.add(item)
            session.add(state)
            session.commit()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Upgrade common data coverage for active tickers.")
    parser.add_argument("--years", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(upgrade(args.years)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
