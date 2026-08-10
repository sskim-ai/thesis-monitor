import json
from datetime import date, datetime, timezone

from sqlmodel import Session, select

from app.config import get_settings
from app.models.thesis import InvestmentThesis, MonitorRun, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import DailyMonitorResponse, PriceContext
from app.services.collection_service import CollectionService
from app.services.local_storage import export_assessment_history, export_monitor_run, export_thesis
from app.services.monitoring_service import assessment_to_read
from app.services.notification_service import dispatch_pending_notifications, queue_notification
from app.services.ohlcv_client import OhlcvClient
from app.services.thesis_evaluation_service import evaluate_thesis, recent_events_for_assessment


def _latest_thesis(session: Session, ticker: str) -> InvestmentThesis | None:
    return session.exec(
        select(InvestmentThesis)
        .where(InvestmentThesis.ticker == ticker, InvestmentThesis.status == "active")
        .order_by(InvestmentThesis.version.desc())
    ).first()


def _assessment_for_date(
    session: Session,
    ticker: str,
    run_date: date,
) -> ThesisAssessment | None:
    return session.exec(
        select(ThesisAssessment).where(
            ThesisAssessment.ticker == ticker,
            ThesisAssessment.assessment_date == run_date,
        )
    ).first()


def _previous_snapshot(session: Session, ticker: str, run_date: date) -> dict[str, object]:
    previous = session.exec(
        select(ThesisAssessment)
        .where(
            ThesisAssessment.ticker == ticker,
            ThesisAssessment.assessment_date < run_date,
        )
        .order_by(ThesisAssessment.assessment_date.desc())
    ).first()
    if previous is None:
        return {}
    try:
        parsed = json.loads(previous.thesis_snapshot)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _json_value(value: str, fallback: object) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _merge_evidence(
    previous: object,
    current: list[dict[str, object]],
    directions: set[str],
) -> list[dict[str, object]]:
    merged = list(previous) if isinstance(previous, list) else []
    seen = {str(item.get("url")) for item in merged if isinstance(item, dict)}
    for item in current:
        if item.get("direction") not in directions:
            continue
        url = str(item.get("url"))
        if url not in seen:
            merged.append(item)
            seen.add(url)
    return merged[-100:]


def _build_thesis_snapshot(
    session: Session,
    thesis: InvestmentThesis,
    run_date: date,
    status: str,
    summary: str,
    evidence: list[dict[str, object]],
) -> dict[str, object]:
    previous = _previous_snapshot(session, thesis.ticker, run_date)
    return {
        "base_thesis": thesis.core_thesis,
        "thesis_version": thesis.version,
        "effective_date": str(run_date),
        "status": status,
        "current_thesis": f"{thesis.core_thesis} 현재 평가: {summary}",
        "thesis_drivers": _json_value(thesis.thesis_drivers, []),
        "validation_metrics": _json_value(thesis.validation_metrics, []),
        "price_rules": _json_value(thesis.price_rules, {}),
        "supporting_evidence": _merge_evidence(
            previous.get("supporting_evidence"), evidence, {"strengthen"}
        ),
        "weakening_evidence": _merge_evidence(
            previous.get("weakening_evidence"), evidence, {"weaken"}
        ),
        "invalidation_evidence": _merge_evidence(
            previous.get("invalidation_evidence"), evidence, {"invalidation"}
        ),
    }


async def run_daily_monitor(
    session: Session,
    run_date: date | None = None,
    force: bool = False,
    collection_service: CollectionService | None = None,
    price_client: OhlcvClient | None = None,
) -> DailyMonitorResponse:
    run_date = run_date or date.today()
    existing_run = session.exec(
        select(MonitorRun).where(MonitorRun.run_date == run_date, MonitorRun.run_type == "daily")
    ).first()
    if existing_run is not None and existing_run.status == "success" and not force:
        await dispatch_pending_notifications(session)
        assessments = session.exec(
            select(ThesisAssessment).where(ThesisAssessment.assessment_date == run_date)
        ).all()
        return DailyMonitorResponse(
            run_date=run_date,
            status="already_completed",
            ticker_count=existing_run.ticker_count,
            success_count=existing_run.success_count,
            failure_count=existing_run.failure_count,
            assessments=[assessment_to_read(item) for item in assessments],
        )

    run = existing_run or MonitorRun(run_date=run_date, run_type="daily")
    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    run.completed_at = None
    run.success_count = 0
    run.failure_count = 0
    session.add(run)
    session.commit()

    collection_service = collection_service or CollectionService()
    price_client = price_client or OhlcvClient()
    settings = get_settings()
    watchlist = session.exec(
        select(WatchlistItem)
        .where(WatchlistItem.active.is_(True))
        .order_by(WatchlistItem.ticker)
    ).all()
    run.ticker_count = len(watchlist)
    details: dict[str, object] = {"tickers": {}}
    completed_assessments: list[ThesisAssessment] = []

    for item in watchlist:
        thesis = _latest_thesis(session, item.ticker)
        if thesis is None:
            details["tickers"][item.ticker] = {"status": "skipped", "reason": "no_active_thesis"}
            continue
        try:
            await collection_service.collect_events(
                session,
                item.ticker,
                settings.monitor_lookback_days,
            )
            try:
                price_context = await price_client.fetch_price_context(item.ticker)
            except Exception as exc:  # noqa: BLE001
                price_context = PriceContext(warnings=[f"price_context: {type(exc).__name__}"])
            events = recent_events_for_assessment(session, item.ticker, run_date)
            result = evaluate_thesis(thesis, events, price_context)
            thesis_snapshot = _build_thesis_snapshot(
                session,
                thesis,
                run_date,
                result.status,
                result.summary,
                result.evidence,
            )
            assessment = _assessment_for_date(session, item.ticker, run_date)
            if assessment is None:
                assessment = ThesisAssessment(
                    ticker=item.ticker,
                    thesis_version=thesis.version,
                    assessment_date=run_date,
                    status=result.status,
                    score=result.score,
                    confidence=result.confidence,
                    summary=result.summary,
                    new_buyer_view=result.new_buyer_view,
                    holder_view=result.holder_view,
                    price_view=result.price_view,
                    risk_level=result.risk_level,
                    evidence=json.dumps(result.evidence, ensure_ascii=False),
                    price_context=price_context.model_dump_json(),
                    thesis_snapshot=json.dumps(thesis_snapshot, ensure_ascii=False),
                )
                session.add(assessment)
            else:
                assessment.thesis_version = thesis.version
                assessment.status = result.status
                assessment.score = result.score
                assessment.confidence = result.confidence
                assessment.summary = result.summary
                assessment.new_buyer_view = result.new_buyer_view
                assessment.holder_view = result.holder_view
                assessment.price_view = result.price_view
                assessment.risk_level = result.risk_level
                assessment.evidence = json.dumps(result.evidence, ensure_ascii=False)
                assessment.price_context = price_context.model_dump_json()
                assessment.thesis_snapshot = json.dumps(thesis_snapshot, ensure_ascii=False)
            if result.should_deactivate:
                item.active = False
                thesis.status = "invalidated"
            session.commit()
            session.refresh(assessment)
            if result.should_deactivate:
                export_thesis(thesis)
            queue_notification(session, assessment)
            session.commit()
            export_assessment_history(session, item.ticker)
            completed_assessments.append(assessment)
            run.success_count += 1
            details["tickers"][item.ticker] = {
                "status": result.status,
                "event_count": len(events),
                "price_period_counts": {
                    period: summary.actual_count
                    for period, summary in price_context.periods.items()
                },
            }
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            run.failure_count += 1
            details["tickers"][item.ticker] = {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }

    if run.failure_count and run.success_count:
        run.status = "partial"
    elif run.failure_count:
        run.status = "failed"
    else:
        run.status = "success"
    run.completed_at = datetime.now(timezone.utc)
    run.details = json.dumps(details, ensure_ascii=False)
    session.add(run)
    session.commit()
    session.refresh(run)
    export_monitor_run(run)
    await dispatch_pending_notifications(session)
    return DailyMonitorResponse(
        run_date=run_date,
        status=run.status,
        ticker_count=run.ticker_count,
        success_count=run.success_count,
        failure_count=run.failure_count,
        assessments=[assessment_to_read(item) for item in completed_assessments],
    )
