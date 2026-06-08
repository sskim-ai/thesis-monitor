from sqlmodel import Session, select

from app.models.company import Company
from app.models.watchlist import WatchlistItem
from app.schemas.watchlist import WatchlistItemCreate


def add_watchlist_item(session: Session, payload: WatchlistItemCreate) -> WatchlistItem:
    ticker = payload.ticker.upper()
    existing = session.exec(select(WatchlistItem).where(WatchlistItem.ticker == ticker)).first()
    if existing:
        existing.company_name = payload.company_name
        existing.exchange = payload.exchange
        existing.notes = payload.notes
        item = existing
    else:
        item = WatchlistItem(
            ticker=ticker,
            company_name=payload.company_name,
            exchange=payload.exchange,
            notes=payload.notes,
        )
        session.add(item)

    company = session.exec(select(Company).where(Company.ticker == ticker)).first()
    if company is None:
        session.add(
            Company(
                ticker=ticker,
                company_name=payload.company_name,
                exchange=payload.exchange,
                ir_url=None,
                filings_url=None,
            )
        )

    session.commit()
    session.refresh(item)
    return item


def list_watchlist_items(session: Session) -> list[WatchlistItem]:
    return list(session.exec(select(WatchlistItem).order_by(WatchlistItem.ticker)).all())

