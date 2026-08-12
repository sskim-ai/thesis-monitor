from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.security import require_action_api_key
from app.database import get_session
from app.schemas.admin import ReclassifyEventsResponse
from app.schemas.thesis import DailyMonitorResponse
from app.services.daily_monitor_service import run_daily_monitor
from app.services.financial_backfill_service import backfill_financial_snapshots
from app.services.reclassification_service import reclassify_events
from app.macro.service import run_macro_monitor
from app.schemas.macro import MacroMonitorResponse

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_action_api_key)],
)


@router.post("/run-macro-monitor", response_model=MacroMonitorResponse)
async def run_macro_monitor_now(
    force: bool = Query(False),
    session: Session = Depends(get_session),
) -> MacroMonitorResponse:
    return await run_macro_monitor(session=session, force=force)


@router.post("/run-daily-monitor", response_model=DailyMonitorResponse)
async def run_daily_monitor_now(
    force: bool = Query(False),
    market: Literal["us", "kr", "all"] = Query("all"),
    session: Session = Depends(get_session),
) -> DailyMonitorResponse:
    return await run_daily_monitor(session=session, force=force, market_scope=market)


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


@router.post("/backfill-financial-snapshots", operation_id="backfillFinancialSnapshots")
async def backfill_financial_snapshot_rows(
    ticker: str = Query(..., min_length=1),
    years: int = Query(5, ge=1, le=10),
    provider: str = Query("opendart", min_length=1),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    result = await backfill_financial_snapshots(
        session=session,
        ticker=ticker,
        years=years,
        provider=provider,
    )
    return {
        "ticker": result.ticker,
        "provider": result.provider,
        "years": result.years,
        "scanned_count": result.scanned_count,
        "report_count": result.report_count,
        "backfilled_count": result.backfilled_count,
        "skipped_count": result.skipped_count,
        "periods": result.periods,
        "warnings": result.warnings,
    }
