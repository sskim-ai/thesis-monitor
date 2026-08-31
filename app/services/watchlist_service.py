from sqlmodel import Session, select

from app.models.company import Company
from app.models.watchlist import WatchlistItem
from app.schemas.watchlist import WatchlistItemCreate
from app.services.onboarding_readiness_service import (
    begin_onboarding,
    deactivate_onboarding,
    reconcile_onboarding,
)
from app.utils.tickers import normalize_ticker


def add_watchlist_item(session: Session, payload: WatchlistItemCreate) -> WatchlistItem:
    ticker = normalize_ticker(payload.ticker)
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
            active=False,
            monitoring_requested=payload.active,
            production_eligible=False,
            onboarding_state="PENDING_ONBOARDING",
        )
        session.add(item)
    if payload.active:
        if not (
            existing
            and item.active
            and item.production_eligible
            and item.onboarding_state == "ACTIVE"
        ):
            begin_onboarding(item)
    else:
        deactivate_onboarding(item)

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

    session.flush()
    if payload.active:
        reconcile_onboarding(session, item)
    session.commit()
    session.refresh(item)
    return item


def list_watchlist_items(session: Session) -> list[WatchlistItem]:
    return list(session.exec(select(WatchlistItem).order_by(WatchlistItem.ticker)).all())
