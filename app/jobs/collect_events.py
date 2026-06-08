from sqlmodel import Session

from app.database import engine
from app.services.collection_service import CollectionService


async def collect_watchlist_events(tickers: list[str], lookback_days: int = 7) -> None:
    service = CollectionService()
    with Session(engine) as session:
        for ticker in tickers:
            await service.collect_events(session, ticker, lookback_days)

