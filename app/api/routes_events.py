from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.event import ThesisEventResponse
from app.services.collection_service import CollectionService

router = APIRouter()
collection_service = CollectionService()


@router.get("/thesis-events", response_model=ThesisEventResponse, operation_id="getThesisEvents")
async def get_thesis_events(
    ticker: str = Query(..., min_length=1),
    lookback_days: int = Query(30, ge=1, le=365),
    requires_review_only: bool = Query(False),
    provider: str | None = Query(None, min_length=1),
    session: Session = Depends(get_session),
) -> ThesisEventResponse:
    return await collection_service.get_thesis_events(
        session=session,
        ticker=ticker,
        lookback_days=lookback_days,
        requires_review_only=requires_review_only,
        provider=provider,
    )
