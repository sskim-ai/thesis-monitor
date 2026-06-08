from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.financial import EarningsCheckpointResponse
from app.services.collection_service import CollectionService

router = APIRouter()
collection_service = CollectionService()


@router.get(
    "/earnings-checkpoints",
    response_model=EarningsCheckpointResponse,
    operation_id="getEarningsCheckpoints",
)
async def get_earnings_checkpoints(
    ticker: str = Query(..., min_length=1), session: Session = Depends(get_session)
) -> EarningsCheckpointResponse:
    return await collection_service.get_earnings_checkpoints(session, ticker)
