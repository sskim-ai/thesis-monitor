from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.api.security import require_action_api_key
from app.database import get_session
from app.schemas.thesis import (
    MonitoringItemCreate,
    MonitoringItemRead,
    MonitoringItemSummaryRead,
    ThesisAssessmentRead,
)
from app.services.monitoring_service import (
    deactivate_monitoring_item,
    get_monitoring_item,
    list_assessments,
    list_monitoring_items,
    list_monitoring_summaries,
    register_monitoring_item,
)

router = APIRouter(
    prefix="/monitoring-items",
    tags=["monitoring"],
    dependencies=[Depends(require_action_api_key)],
)


@router.post(
    "",
    response_model=MonitoringItemRead,
    operation_id="monitorStock",
    summary="Start or update thesis monitoring for a stock",
    description=(
        "Use when the user says a stock should be monitored going forward. First collect current "
        "company evidence and construct a concrete thesis. Changed thesis fields create a new "
        "version; an identical request is idempotent."
    ),
)
def monitor_stock(
    payload: MonitoringItemCreate,
    session: Session = Depends(get_session),
) -> MonitoringItemRead:
    return register_monitoring_item(session, payload)


@router.get(
    "",
    response_model=list[MonitoringItemRead],
    operation_id="listMonitoredStocks",
    summary="List monitored stocks and their current theses",
)
def monitored_stocks(
    active_only: bool = Query(True),
    session: Session = Depends(get_session),
) -> list[MonitoringItemRead]:
    return list_monitoring_items(session, active_only=active_only)


@router.get(
    "/summaries",
    response_model=list[MonitoringItemSummaryRead],
    operation_id="listMonitoredStockSummaries",
    summary="List monitored stocks with compact current investment logic",
)
def monitored_stock_summaries(
    active_only: bool = Query(True),
    session: Session = Depends(get_session),
) -> list[MonitoringItemSummaryRead]:
    return list_monitoring_summaries(session, active_only=active_only)


@router.get("/{ticker}", response_model=MonitoringItemRead, operation_id="getMonitoredStock")
def monitored_stock(ticker: str, session: Session = Depends(get_session)) -> MonitoringItemRead:
    result = get_monitoring_item(session, ticker)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticker is not monitored.")
    return result


@router.post(
    "/{ticker}/deactivate",
    response_model=MonitoringItemRead,
    operation_id="stopMonitoringStock",
    summary="Stop monitoring a stock without deleting its history",
)
def stop_monitoring_stock(
    ticker: str,
    session: Session = Depends(get_session),
) -> MonitoringItemRead:
    result = deactivate_monitoring_item(session, ticker)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticker is not monitored.")
    return result


@router.get(
    "/{ticker}/assessments",
    response_model=list[ThesisAssessmentRead],
    operation_id="getThesisAssessmentHistory",
)
def assessment_history(
    ticker: str,
    limit: int = Query(30, ge=1, le=365),
    session: Session = Depends(get_session),
) -> list[ThesisAssessmentRead]:
    return list_assessments(session, ticker, limit=limit)
