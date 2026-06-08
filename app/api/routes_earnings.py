from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.financial import EarningsCheckpoint
from app.services.collection_service import CollectionService

router = APIRouter()
collection_service = CollectionService()


@router.get(
    "/earnings-checkpoints",
    response_model=list[EarningsCheckpoint],
    operation_id="getEarningsCheckpoints",
)
def get_earnings_checkpoints(
    ticker: str = Query(..., min_length=1), session: Session = Depends(get_session)
) -> list[EarningsCheckpoint]:
    return collection_service.get_earnings_checkpoints(session, ticker)

