from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.company import CompanyProfile
from app.services.collection_service import CollectionService

router = APIRouter()
collection_service = CollectionService()


@router.get("/company-profile", response_model=CompanyProfile, operation_id="getCompanyProfile")
async def get_company_profile(
    ticker: str = Query(..., min_length=1), session: Session = Depends(get_session)
) -> CompanyProfile:
    return await collection_service.get_company_profile(session, ticker)
