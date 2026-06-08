from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.admin import ReclassifyEventsResponse
from app.services.reclassification_service import reclassify_events

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/reclassify-events",
    response_model=ReclassifyEventsResponse,
    operation_id="reclassifyEvents",
)
def reclassify_event_rows(
    ticker: str | None = Query(None, min_length=1),
    provider: str | None = Query(None, min_length=1),
    dry_run: bool = Query(True),
    session: Session = Depends(get_session),
) -> ReclassifyEventsResponse:
    result = reclassify_events(session=session, ticker=ticker, provider=provider, dry_run=dry_run)
    return ReclassifyEventsResponse(
        ticker=ticker.upper() if ticker else None,
        provider=provider,
        dry_run=dry_run,
        scanned_count=result.scanned_count,
        changed_count=result.changed_count,
        updated_count=result.updated_count,
    )
