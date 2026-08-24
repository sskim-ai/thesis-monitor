from datetime import date, datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

from app.config import get_settings
from app.macro.briefing import briefing_to_dict, build_macro_briefing
from app.macro.impact import assess_thesis_macro_impacts
from app.macro.providers.base import MacroProvider
from app.macro.providers.registry import macro_provider_statuses, macro_providers
from app.macro.regime import assess_macro_regime
from app.macro.shocks import assess_macro_shocks
from app.macro.storage import collect_macro_data
from app.macro.temporal import build_session_temporal_context
from app.macro.theses import update_macro_theses
from app.models.macro import MacroBriefing
from app.schemas.macro import MacroBriefingRead, MacroMonitorResponse
from app.services.local_storage import export_macro_briefing
from app.services.notification_service import dispatch_pending_notifications, queue_macro_notification


async def run_macro_monitor(
    session: Session,
    run_date: date | None = None,
    force: bool = False,
    providers: list[MacroProvider] | None = None,
    excluded_provider_names: set[str] | None = None,
    as_of: datetime | None = None,
    queue_notifications: bool = True,
    dispatch_notifications: bool = True,
) -> MacroMonitorResponse:
    run_date = run_date or date.today()
    as_of = as_of or datetime.now(timezone.utc)
    existing = session.exec(
        select(MacroBriefing).where(
            MacroBriefing.briefing_date == run_date,
            MacroBriefing.briefing_type == "morning",
        )
    ).first()
    if existing is not None and existing.status == "ready" and not force:
        delivery = None
        if queue_notifications:
            delivery = queue_macro_notification(session, existing)
        session.commit()
        if (
            queue_notifications
            and dispatch_notifications
            and delivery is not None
            and delivery.id is not None
        ):
            await dispatch_pending_notifications(session, delivery_ids={delivery.id})
        return MacroMonitorResponse(
            run_date=run_date,
            status="already_completed",
            observation_count=0,
            event_count=0,
            impact_count=len(briefing_to_dict(existing)["ticker_impacts"]),
            briefing=MacroBriefingRead.model_validate(briefing_to_dict(existing)),
        )

    selected_providers = providers if providers is not None else macro_providers()
    if excluded_provider_names:
        selected_providers = [
            provider
            for provider in selected_providers
            if provider.name not in excluded_provider_names
        ]
    observation_count, event_count, warnings = await collect_macro_data(
        session, selected_providers, as_of
    )
    if providers is None:
        warnings.extend(
            f"{item.name}: not configured ({', '.join(item.required_settings)})"
            for item in macro_provider_statuses()
            if item.enabled and not item.configured
        )
    temporal_context = build_session_temporal_context(
        session,
        briefing_date=run_date,
        as_of=as_of,
    )
    eligible_series = {
        str(item) for item in temporal_context.get("current_series", [])
    }
    daily_axes = {
        str(key): int(value)
        for key, value in dict(temporal_context.get("daily_axes", {})).items()
    }
    assess_macro_shocks(session, run_date, eligible_series)
    regime = assess_macro_regime(session, run_date, as_of=as_of)
    theses = update_macro_theses(session, regime, daily_axes)
    impacts = assess_thesis_macro_impacts(session, run_date, eligible_series)
    briefing = build_macro_briefing(
        session,
        briefing_date=run_date,
        as_of=as_of,
        regime=regime,
        theses=theses,
        impacts=impacts,
        provider_warnings=warnings,
        temporal_context=temporal_context,
    )
    briefing.status = "partial" if warnings else "ready"
    session.add(briefing)
    delivery = queue_macro_notification(session, briefing) if queue_notifications else None
    session.commit()
    export_macro_briefing(briefing)
    if (
        queue_notifications
        and dispatch_notifications
        and delivery is not None
        and delivery.id is not None
    ):
        await dispatch_pending_notifications(session, delivery_ids={delivery.id})
    return MacroMonitorResponse(
        run_date=run_date,
        status=briefing.status,
        observation_count=observation_count,
        event_count=event_count,
        impact_count=len(impacts),
        provider_warnings=warnings,
        briefing=MacroBriefingRead.model_validate(briefing_to_dict(briefing)),
    )


def macro_runtime_summary() -> dict[str, object]:
    settings = get_settings()
    return {
        "enabled": settings.macro_monitor_enabled,
        "data_root": str(Path(settings.data_dir) / "macro"),
        "providers": [item.name for item in macro_provider_statuses() if item.configured],
    }
