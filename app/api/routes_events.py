from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.event import ThesisEventResponse
from app.services.collection_service import CollectionService

router = APIRouter()
collection_service = CollectionService()


@router.get(
    "/thesis-events",
    response_model=ThesisEventResponse,
    operation_id="getThesisEvents",
    summary="Collect and return investment evidence for one stock",
    description=(
        "Use this operation for the current user's stock analysis. It accepts a six-digit Korean "
        "stock code, a supported Korean company name, or a US ticker. For Korean disclosures, "
        "set provider=opendart. If a name-based request fails, resolve the stock code and retry "
        "once. Do not describe this operation as unavailable unless a call in the current turn "
        "actually returns an error."
    ),
)
async def get_thesis_events(
    ticker: str = Query(..., min_length=1),
    lookback_days: int = Query(30, ge=1, le=365),
    requires_review_only: bool = Query(False),
    provider: str | None = Query(None, min_length=1),
    auto_backfill: bool = Query(False),
    backfill_years: int = Query(5, ge=1, le=10),
    session: Session = Depends(get_session),
) -> ThesisEventResponse:
    return await collection_service.get_thesis_events(
        session=session,
        ticker=ticker,
        lookback_days=lookback_days,
        requires_review_only=requires_review_only,
        provider=provider,
        auto_backfill=auto_backfill,
        backfill_years=backfill_years,
    )
