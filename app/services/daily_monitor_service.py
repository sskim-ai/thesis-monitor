import json
import logging
from datetime import date, datetime, timezone

from sqlmodel import Session, select

from app.config import get_settings
from app.models.macro import ThesisMacroImpact
from app.models.thesis import InvestmentThesis, MonitorRun, ThesisAssessment
from app.models.security import SecurityMaster
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import DailyMonitorResponse, PriceContext
from app.services.collection_service import CollectionService
from app.services.event_identity import event_fingerprint
from app.services.event_materiality_service import treasury_stock_materiality
from app.services.local_storage import export_assessment_history, export_monitor_run, export_thesis
from app.services.market_session import MarketScope, market_scope_for_security
from app.services.monitoring_service import assessment_to_read
from app.services.notification_service import (
    dispatch_pending_notifications,
    queue_daily_digest_notification,
    queue_daily_stock_notification,
)
from app.services.ohlcv_client import OhlcvClient
from app.services.issue_identity_audit_service import IssueIdentityAuditService
from app.services.thesis_evaluation_service import evaluate_thesis, recent_events_for_assessment
from app.services.valuation_snapshot_service import ValuationSnapshotService
from app.services.warning_backfill_service import backfill_confirmed_warning_states


logger = logging.getLogger(__name__)


def _run_type(market_scope: MarketScope) -> str:
    return "daily" if market_scope == "all" else f"daily_{market_scope}"


def _item_market_scope(session: Session, item: WatchlistItem) -> str:
    security = session.exec(
        select(SecurityMaster).where(SecurityMaster.ticker == item.ticker)
    ).first()
    exchange = item.exchange or (security.exchange if security else None)
    return market_scope_for_security(item.ticker, exchange)


def _watchlist_for_scope(
    session: Session,
    market_scope: MarketScope,
    *,
    active_only: bool,
) -> list[WatchlistItem]:
    query = select(WatchlistItem).order_by(WatchlistItem.ticker)
    if active_only:
        query = query.where(WatchlistItem.active.is_(True))
    items = list(session.exec(query).all())
    if market_scope == "all":
        return items
    return [item for item in items if _item_market_scope(session, item) == market_scope]


def _queue_scoped_notifications(
    session: Session,
    run_date: date,
    assessments: list[ThesisAssessment],
    market_scope: MarketScope,
    requeue_sent_before: datetime | None,
) -> set[int]:
    deliveries = [
        queue_daily_digest_notification(
            session,
            run_date,
            market_scope=market_scope,
            requeue_sent_before=requeue_sent_before,
        )
    ]
    deliveries.extend(
        queue_daily_stock_notification(
            session,
            assessment,
            requeue_sent_before=requeue_sent_before,
        )
        for assessment in assessments
    )
    session.commit()
    return {delivery.id for delivery in deliveries if delivery is not None and delivery.id is not None}


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


def _previous_assessment(
    session: Session,
    ticker: str,
    run_date: date,
    thesis_version: int | None = None,
) -> ThesisAssessment | None:
    query = select(ThesisAssessment).where(
        ThesisAssessment.ticker == ticker,
        ThesisAssessment.assessment_date < run_date,
    )
    if thesis_version is not None:
        query = query.where(ThesisAssessment.thesis_version == thesis_version)
    return session.exec(query.order_by(ThesisAssessment.assessment_date.desc())).first()


def _is_initial_baseline(
    session: Session,
    ticker: str,
    thesis_version: int,
    run_date: date,
    *,
    has_new_events: bool,
) -> bool:
    same_date = session.exec(
        select(ThesisAssessment).where(
            ThesisAssessment.ticker == ticker,
            ThesisAssessment.thesis_version == thesis_version,
            ThesisAssessment.assessment_date == run_date,
        )
    ).first()
    if same_date is not None:
        snapshot = _json_value(same_date.thesis_snapshot, {})
        if snapshot.get("assessment_mode") == "initial_baseline":
            return not has_new_events
        if has_new_events:
            return False
        return _previous_assessment(session, ticker, run_date, thesis_version) is None
    return _previous_assessment(session, ticker, run_date, thesis_version) is None


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
    valuation_context: dict[str, object],
    new_confirmed_facts: list[str],
    background_confirmed_facts: list[str],
    assessment_mode: str,
    baseline_event_count: int,
    delta_event_count: int,
    capital_action_materiality: list[dict[str, object]],
) -> dict[str, object]:
    previous = _previous_snapshot(session, thesis.ticker, run_date)
    return {
        "base_thesis": thesis.core_thesis,
        "thesis_version": thesis.version,
        "effective_date": str(run_date),
        "status": status,
        "assessment_mode": assessment_mode,
        "baseline_event_count": baseline_event_count,
        "delta_event_count": delta_event_count,
        "capital_action_materiality": capital_action_materiality,
        "current_thesis": f"{thesis.core_thesis} 현재 평가: {summary}",
        "thesis_drivers": _json_value(thesis.thesis_drivers, []),
        "validation_metrics": _json_value(thesis.validation_metrics, []),
        "price_rules": _json_value(thesis.price_rules, {}),
        "market_expectations": _json_value(thesis.market_expectations, {}),
        "valuation_framework": _json_value(thesis.valuation_framework, {}),
        "multiple_expansion_signals": _json_value(thesis.multiple_expansion_signals, []),
        "multiple_compression_signals": _json_value(
            thesis.multiple_compression_signals, []
        ),
        "valuation_context": valuation_context,
        "new_confirmed_facts": new_confirmed_facts,
        "background_confirmed_facts": background_confirmed_facts,
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
    valuation_service: ValuationSnapshotService | None = None,
    queue_notifications: bool = True,
    dispatch_notifications: bool = True,
    requeue_sent_before: datetime | None = None,
    market_scope: MarketScope = "all",
    as_of: datetime | None = None,
) -> DailyMonitorResponse:
    run_date = run_date or date.today()
    run_type = _run_type(market_scope)
    scoped_items = _watchlist_for_scope(session, market_scope, active_only=True)
    scoped_tickers = {item.ticker for item in _watchlist_for_scope(
        session, market_scope, active_only=False
    )}
    existing_run = session.exec(
        select(MonitorRun).where(MonitorRun.run_date == run_date, MonitorRun.run_type == run_type)
    ).first()
    if existing_run is not None and existing_run.status == "running" and not force:
        return DailyMonitorResponse(
            run_date=run_date,
            status="analysis_in_progress",
            ticker_count=existing_run.ticker_count,
            success_count=existing_run.success_count,
            failure_count=existing_run.failure_count,
            assessments=[],
        )
    if existing_run is not None and existing_run.status == "success" and not force:
        assessments = list(
            session.exec(
                select(ThesisAssessment).where(
                    ThesisAssessment.assessment_date == run_date,
                    ThesisAssessment.ticker.in_(scoped_tickers),
                )
            ).all()
        ) if scoped_tickers else []
        delivery_ids: set[int] = set()
        if queue_notifications:
            delivery_ids = _queue_scoped_notifications(
                session, run_date, assessments, market_scope, requeue_sent_before
            )
        if queue_notifications and dispatch_notifications:
            await dispatch_pending_notifications(session, delivery_ids=delivery_ids)
        return DailyMonitorResponse(
            run_date=run_date,
            status="already_completed",
            ticker_count=existing_run.ticker_count,
            success_count=existing_run.success_count,
            failure_count=existing_run.failure_count,
            assessments=[assessment_to_read(item) for item in assessments],
        )

    run = existing_run or MonitorRun(run_date=run_date, run_type=run_type)
    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    run.completed_at = None
    run.success_count = 0
    run.failure_count = 0
    session.add(run)
    session.commit()

    collection_service = collection_service or CollectionService()
    price_client = price_client or OhlcvClient()
    valuation_service = valuation_service or ValuationSnapshotService()
    settings = get_settings()
    watchlist = scoped_items
    run.ticker_count = len(watchlist)
    unknown_tickers = [
        item.ticker
        for item in _watchlist_for_scope(session, "all", active_only=True)
        if _item_market_scope(session, item) == "unknown"
    ]
    details: dict[str, object] = {
        "market_scope": market_scope,
        "market_scope_unknown": unknown_tickers,
        "tickers": {},
    }
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
                if isinstance(price_client, OhlcvClient):
                    price_context = await price_client.fetch_price_context(
                        item.ticker, as_of=as_of, session=session
                    )
                else:
                    price_context = await price_client.fetch_price_context(item.ticker)
            except Exception as exc:  # noqa: BLE001
                price_context = PriceContext(warnings=[f"price_context: {type(exc).__name__}"])
            valuation_snapshot = await valuation_service.fetch(
                item.ticker,
                item.exchange,
                price_context,
                session=session,
                thesis=thesis,
            )
            IssueIdentityAuditService().audit(session, item.ticker)
            all_recent_events = recent_events_for_assessment(
                session, item.ticker, run_date
            )
            assessment_mode = (
                "initial_baseline"
                if _is_initial_baseline(
                    session,
                    item.ticker,
                    thesis.version,
                    run_date,
                    has_new_events=bool(all_recent_events),
                )
                else "daily_delta"
            )
            current_price = price_context.decision.current_price
            materiality_by_fingerprint: dict[str, str] = {}
            materiality_audit: list[dict[str, object]] = []
            evaluation_events = []
            for event in all_recent_events:
                materiality = treasury_stock_materiality(
                    session, event, current_price
                )
                if materiality is not None:
                    fingerprint = event_fingerprint(event)
                    materiality_by_fingerprint[fingerprint] = materiality.level
                    materiality_audit.append(
                        {
                            "event_fingerprint": fingerprint,
                            "event_date": str(event.date),
                            "event_title": event.title,
                            **materiality.audit_dict(),
                        }
                    )
                    if materiality.level == "immaterial":
                        continue
                evaluation_events.append(event)
            previous_assessment = _previous_assessment(
                session, item.ticker, run_date, thesis.version
            )
            baseline_warning_states = backfill_confirmed_warning_states(
                session, thesis, run_date
            )
            macro_impact = session.exec(
                select(ThesisMacroImpact).where(
                    ThesisMacroImpact.ticker == item.ticker,
                    ThesisMacroImpact.thesis_version == thesis.version,
                    ThesisMacroImpact.assessment_date == run_date,
                )
            ).first()
            result = evaluate_thesis(
                thesis,
                evaluation_events,
                price_context,
                macro_impact=macro_impact,
                previous_assessment=previous_assessment,
                valuation_snapshot=valuation_snapshot,
                baseline_warning_states=baseline_warning_states,
                assessment_mode=assessment_mode,
                event_materiality=materiality_by_fingerprint,
            )
            result.used_event_fingerprints = list(
                dict.fromkeys(
                    [
                        *result.used_event_fingerprints,
                        *(event_fingerprint(event) for event in all_recent_events),
                    ]
                )
            )
            valuation_context = result.valuation_context.model_dump(mode="json")
            thesis_snapshot = _build_thesis_snapshot(
                session,
                thesis,
                run_date,
                result.status,
                result.summary,
                result.evidence,
                valuation_context,
                result.confirmed_facts,
                result.background_confirmed_facts,
                assessment_mode,
                len(all_recent_events) if assessment_mode == "initial_baseline" else 0,
                len(evaluation_events) if assessment_mode == "daily_delta" else 0,
                materiality_audit,
            )
            assessment = _assessment_for_date(session, item.ticker, run_date)
            if assessment is None:
                assessment = ThesisAssessment(
                    ticker=item.ticker,
                    thesis_version=thesis.version,
                    assessment_date=run_date,
                    status=result.status,
                    business_thesis_change=result.status.value,
                    valuation_change=result.valuation_context.impact.value,
                    earnings_estimate_impact=result.earnings_estimate_impact.value,
                    market_expectation_assessment=result.market_expectation_assessment.model_dump_json(),
                    confirmed_facts=json.dumps(result.confirmed_facts, ensure_ascii=False),
                    background_confirmed_facts=json.dumps(
                        result.background_confirmed_facts, ensure_ascii=False
                    ),
                    inferred_implications=json.dumps(
                        result.inferred_implications, ensure_ascii=False
                    ),
                    unknowns=json.dumps(result.unknowns, ensure_ascii=False),
                    confirmed_warnings=json.dumps(result.confirmed_warnings, ensure_ascii=False),
                    new_warnings=json.dumps(result.new_warnings, ensure_ascii=False),
                    open_warnings=json.dumps(result.open_warnings, ensure_ascii=False),
                    open_confirmed_warnings=json.dumps(
                        result.open_confirmed_warnings, ensure_ascii=False
                    ),
                    persistent_watch_risks=json.dumps(
                        result.persistent_watch_risks, ensure_ascii=False
                    ),
                    warning_states=json.dumps(result.warning_states, ensure_ascii=False),
                    watch_items=json.dumps(result.watch_items, ensure_ascii=False),
                    used_event_fingerprints=json.dumps(
                        result.used_event_fingerprints, ensure_ascii=False
                    ),
                    score=result.score,
                    confidence=result.confidence,
                    summary=result.summary,
                    new_buyer_view=result.new_buyer_view,
                    holder_view=result.holder_view,
                    price_view=result.price_view,
                    risk_level=result.risk_level,
                    daily_change_severity=result.daily_change_severity,
                    structural_risk_level=result.structural_risk_level.value,
                    assessment_state=result.assessment_state.value,
                    market_session=result.market_session,
                    new_buyer_price_view=result.new_buyer_price_view,
                    holder_price_view=result.holder_price_view,
                    evidence=json.dumps(result.evidence, ensure_ascii=False),
                    price_context=price_context.model_dump_json(),
                    valuation_snapshot=result.valuation_snapshot.model_dump_json(),
                    valuation_context=json.dumps(valuation_context, ensure_ascii=False),
                    thesis_snapshot=json.dumps(thesis_snapshot, ensure_ascii=False),
                )
                session.add(assessment)
            else:
                assessment.thesis_version = thesis.version
                assessment.status = result.status
                assessment.business_thesis_change = result.status.value
                assessment.valuation_change = result.valuation_context.impact.value
                assessment.earnings_estimate_impact = result.earnings_estimate_impact.value
                assessment.market_expectation_assessment = (
                    result.market_expectation_assessment.model_dump_json()
                )
                assessment.confirmed_facts = json.dumps(
                    result.confirmed_facts, ensure_ascii=False
                )
                assessment.background_confirmed_facts = json.dumps(
                    result.background_confirmed_facts, ensure_ascii=False
                )
                assessment.inferred_implications = json.dumps(
                    result.inferred_implications, ensure_ascii=False
                )
                assessment.unknowns = json.dumps(result.unknowns, ensure_ascii=False)
                assessment.confirmed_warnings = json.dumps(
                    result.confirmed_warnings, ensure_ascii=False
                )
                assessment.new_warnings = json.dumps(result.new_warnings, ensure_ascii=False)
                assessment.open_warnings = json.dumps(result.open_warnings, ensure_ascii=False)
                assessment.open_confirmed_warnings = json.dumps(
                    result.open_confirmed_warnings, ensure_ascii=False
                )
                assessment.persistent_watch_risks = json.dumps(
                    result.persistent_watch_risks, ensure_ascii=False
                )
                assessment.warning_states = json.dumps(
                    result.warning_states, ensure_ascii=False
                )
                assessment.watch_items = json.dumps(result.watch_items, ensure_ascii=False)
                assessment.used_event_fingerprints = json.dumps(
                    result.used_event_fingerprints, ensure_ascii=False
                )
                assessment.score = result.score
                assessment.confidence = result.confidence
                assessment.summary = result.summary
                assessment.new_buyer_view = result.new_buyer_view
                assessment.holder_view = result.holder_view
                assessment.price_view = result.price_view
                assessment.risk_level = result.risk_level
                assessment.daily_change_severity = result.daily_change_severity
                assessment.structural_risk_level = result.structural_risk_level.value
                assessment.assessment_state = result.assessment_state.value
                assessment.market_session = result.market_session
                assessment.new_buyer_price_view = result.new_buyer_price_view
                assessment.holder_price_view = result.holder_price_view
                assessment.evidence = json.dumps(result.evidence, ensure_ascii=False)
                assessment.price_context = price_context.model_dump_json()
                assessment.valuation_snapshot = result.valuation_snapshot.model_dump_json()
                assessment.valuation_context = json.dumps(
                    valuation_context, ensure_ascii=False
                )
                assessment.thesis_snapshot = json.dumps(thesis_snapshot, ensure_ascii=False)
            item.latest_status = result.status.value
            item.latest_assessment_date = run_date
            item.latest_valuation_context = result.valuation_context.impact.value
            item.latest_earnings_estimate_impact = result.earnings_estimate_impact.value
            if result.should_deactivate:
                item.active = False
                thesis.status = "invalidated"
            session.commit()
            session.refresh(assessment)
            if result.should_deactivate:
                export_thesis(thesis)
            export_assessment_history(session, item.ticker)
            completed_assessments.append(assessment)
            run.success_count += 1
            details["tickers"][item.ticker] = {
                "status": result.status,
                "assessment_mode": assessment_mode,
                "event_count": len(all_recent_events),
                "evaluation_event_count": len(evaluation_events),
                "capital_action_materiality": materiality_audit,
                "previous_status": (
                    previous_assessment.business_thesis_change or previous_assessment.status
                    if previous_assessment is not None
                    else None
                ),
                "used_event_fingerprints": result.used_event_fingerprints,
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
    status_counts: dict[str, int] = {}
    for assessment in completed_assessments:
        status = assessment.business_thesis_change or assessment.status
        status_counts[status] = status_counts.get(status, 0) + 1
    material_changes = sum(
        status_counts.get(status, 0)
        for status in {"strengthened", "weakened", "invalidation_candidate", "invalidated"}
    )
    change_ratio = material_changes / len(completed_assessments) if completed_assessments else 0.0
    details["assessment_distribution"] = {
        "material_change_count": material_changes,
        "assessment_count": len(completed_assessments),
        "material_change_ratio": round(change_ratio, 3),
        "status_counts": status_counts,
    }
    if change_ratio > settings.assessment_distribution_warning_threshold:
        warning = (
            "assessment_distribution_warning: unusually high daily thesis-change rate "
            f"({material_changes}/{len(completed_assessments)})"
        )
        details["assessment_distribution_warning"] = warning
        logger.warning(warning)
    non_neutral_valuations = sum(
        1
        for assessment in completed_assessments
        if (assessment.valuation_change or "neutral") != "neutral"
    )
    valuation_ratio = (
        non_neutral_valuations / len(completed_assessments)
        if completed_assessments
        else 0.0
    )
    details["valuation_distribution"] = {
        "non_neutral_count": non_neutral_valuations,
        "assessment_count": len(completed_assessments),
        "non_neutral_ratio": round(valuation_ratio, 3),
    }
    material_macro_valuations = sum(
        1
        for assessment in completed_assessments
        if str(_json_value(assessment.valuation_context, {}).get(
            "macro_valuation_effect", "neutral"
        ))
        != "neutral"
    )
    details["valuation_distribution"]["material_macro_driver_count"] = (
        material_macro_valuations
    )
    unexplained_non_neutral = max(
        0, non_neutral_valuations - material_macro_valuations
    )
    if (
        valuation_ratio > settings.valuation_distribution_warning_threshold
        and unexplained_non_neutral > len(completed_assessments) * 0.3
    ):
        warning = (
            "valuation_distribution_warning: unusually high daily non-neutral rate "
            f"({non_neutral_valuations}/{len(completed_assessments)})"
        )
        details["valuation_distribution_warning"] = warning
        logger.warning(warning)
    run.completed_at = datetime.now(timezone.utc)
    run.details = json.dumps(details, ensure_ascii=False)
    session.add(run)
    session.commit()
    session.refresh(run)
    export_monitor_run(run)
    delivery_ids: set[int] = set()
    if queue_notifications:
        delivery_ids = _queue_scoped_notifications(
            session,
            run_date,
            completed_assessments,
            market_scope,
            requeue_sent_before,
        )
    if queue_notifications and dispatch_notifications:
        await dispatch_pending_notifications(session, delivery_ids=delivery_ids)
    return DailyMonitorResponse(
        run_date=run_date,
        status=run.status,
        ticker_count=run.ticker_count,
        success_count=run.success_count,
        failure_count=run.failure_count,
        assessments=[assessment_to_read(item) for item in completed_assessments],
    )
