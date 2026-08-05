from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.security import require_action_api_key
from app.database import get_session
from app.schemas.watchlist import WatchlistItemCreate, WatchlistItemRead
from app.services.watchlist_service import add_watchlist_item, list_watchlist_items

router = APIRouter(dependencies=[Depends(require_action_api_key)])


@router.post("/watchlist", response_model=WatchlistItemRead, operation_id="addWatchlistItem")
def add_watchlist(
    payload: WatchlistItemCreate, session: Session = Depends(get_session)
) -> WatchlistItemRead:
    return add_watchlist_item(session, payload)


@router.get("/watchlist", response_model=list[WatchlistItemRead], operation_id="getWatchlist")
def get_watchlist(session: Session = Depends(get_session)) -> list[WatchlistItemRead]:
    return list_watchlist_items(session)
