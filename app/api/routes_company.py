from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.company import CompanyProfile, TickerAnalysisSnapshot
from app.services.collection_service import CollectionService
from app.services.ticker_analysis_snapshot_service import (
    TickerAnalysisSnapshotService,
)

router = APIRouter()
collection_service = CollectionService()
analysis_snapshot_service = TickerAnalysisSnapshotService(
    collection_service=collection_service
)


@router.get("/company-profile", response_model=CompanyProfile, operation_id="getCompanyProfile")
async def get_company_profile(
    ticker: str = Query(..., min_length=1), session: Session = Depends(get_session)
) -> CompanyProfile:
    return await collection_service.get_company_profile(session, ticker)


@router.get(
    "/ticker-analysis-snapshot",
    response_model=TickerAnalysisSnapshot,
    operation_id="getTickerAnalysisSnapshot",
)
async def get_ticker_analysis_snapshot(
    ticker: str = Query(..., min_length=1), session: Session = Depends(get_session)
) -> TickerAnalysisSnapshot:
    return await analysis_snapshot_service.fetch(session, ticker)
