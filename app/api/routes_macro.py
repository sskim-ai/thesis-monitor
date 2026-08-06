from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.api.security import require_action_api_key
from app.database import get_session
from app.macro.read_models import (
    macro_briefing_to_read,
    macro_event_to_read,
    macro_impact_to_read,
    macro_regime_to_read,
    macro_thesis_to_read,
)
from app.macro.providers.registry import macro_provider_statuses
from app.models.macro import (
    MacroBriefing,
    MacroEvent,
    MacroObservation,
    MacroRegimeAssessment,
    MacroThesis,
    ThesisMacroImpact,
)
from app.schemas.macro import (
    MacroBriefingRead,
    MacroEventRead,
    MacroObservationRead,
    MacroProviderStatusRead,
    MacroRegimeRead,
    MacroThesisRead,
    ThesisMacroImpactRead,
)
from app.utils.tickers import normalize_ticker


router = APIRouter(
    prefix="/macro",
    tags=["macro"],
    dependencies=[Depends(require_action_api_key)],
)


@router.get(
    "/briefings/latest",
    response_model=MacroBriefingRead,
    operation_id="getMacroBriefing",
)
def latest_macro_briefing(session: Session = Depends(get_session)) -> MacroBriefingRead:
    row = session.exec(
        select(MacroBriefing).order_by(MacroBriefing.briefing_date.desc())
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No macro briefing yet.")
    return macro_briefing_to_read(row)


@router.get(
    "/briefings/{briefing_date}",
    response_model=MacroBriefingRead,
    operation_id="getMacroBriefingByDate",
)
def macro_briefing_by_date(
    briefing_date: date,
    session: Session = Depends(get_session),
) -> MacroBriefingRead:
    row = session.exec(
        select(MacroBriefing).where(MacroBriefing.briefing_date == briefing_date)
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Briefing not found.")
    return macro_briefing_to_read(row)


@router.get(
    "/regime/latest",
    response_model=MacroRegimeRead,
    operation_id="getMacroRegime",
)
def latest_macro_regime(session: Session = Depends(get_session)) -> MacroRegimeRead:
    row = session.exec(
        select(MacroRegimeAssessment).order_by(MacroRegimeAssessment.assessment_date.desc())
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No macro regime yet.")
    return macro_regime_to_read(row)


@router.get("/theses", response_model=list[MacroThesisRead], operation_id="getMacroTheses")
def macro_theses(session: Session = Depends(get_session)) -> list[MacroThesisRead]:
    rows = session.exec(select(MacroThesis).order_by(MacroThesis.thesis_key)).all()
    return [macro_thesis_to_read(row) for row in rows]


@router.get("/events", response_model=list[MacroEventRead], operation_id="getMacroEvents")
def macro_events(
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[MacroEventRead]:
    rows = session.exec(
        select(MacroEvent).order_by(MacroEvent.released_at.desc()).limit(limit)
    ).all()
    return [macro_event_to_read(row) for row in rows]


@router.get("/observations", response_model=list[MacroObservationRead])
def macro_observations(
    series_code: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[MacroObservationRead]:
    query = select(MacroObservation)
    if series_code:
        query = query.where(MacroObservation.series_code == series_code.upper())
    rows = session.exec(query.order_by(MacroObservation.observed_at.desc()).limit(limit)).all()
    return [MacroObservationRead.model_validate(row) for row in rows]


@router.get(
    "/provider-status",
    response_model=list[MacroProviderStatusRead],
    operation_id="getMacroProviderStatus",
)
def macro_provider_status() -> list[MacroProviderStatusRead]:
    return [MacroProviderStatusRead.model_validate(item.__dict__) for item in macro_provider_statuses()]


@router.get(
    "/ticker/{ticker}/impacts",
    response_model=list[ThesisMacroImpactRead],
    operation_id="getTickerMacroImpacts",
)
def ticker_macro_impacts(
    ticker: str,
    limit: int = Query(30, ge=1, le=365),
    session: Session = Depends(get_session),
) -> list[ThesisMacroImpactRead]:
    normalized = normalize_ticker(ticker)
    rows = session.exec(
        select(ThesisMacroImpact)
        .where(ThesisMacroImpact.ticker == normalized)
        .order_by(ThesisMacroImpact.assessment_date.desc())
        .limit(limit)
    ).all()
    return [macro_impact_to_read(row) for row in rows]
