from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import json
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from app.macro.providers.alpha_vantage_fx import AlphaVantageKrCloseFxProvider
from app.macro.providers.base import CollectedObservation
from app.models.macro import MacroBriefing, MacroObservation
from app.services.notification_service import (
    dispatch_pending_notifications,
    queue_macro_notification,
)


KST = ZoneInfo("Asia/Seoul")
FX_SERIES = ("USDKRW_KR_CLOSE", "JPYKRW100_KR_CLOSE", "EURKRW_KR_CLOSE")


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(
        timezone.utc
    )


@dataclass(frozen=True)
class KrCloseBriefingRunResult:
    run_date: date
    status: str
    action: str
    observation_count: int
    warnings: list[str]
    briefing: MacroBriefing | None

    def model_dump(self, mode: str = "python") -> dict[str, object]:
        return {
            "run_date": self.run_date.isoformat() if mode == "json" else self.run_date,
            "status": self.status,
            "action": self.action,
            "observation_count": self.observation_count,
            "warnings": self.warnings,
        }


def previous_kr_close_observation(
    session: Session,
    provider: str,
    series_code: str,
    run_date: date,
) -> MacroObservation | None:
    day_start = datetime.combine(run_date, time.min, tzinfo=KST).astimezone(timezone.utc)
    return session.exec(
        select(MacroObservation)
        .where(
            MacroObservation.provider == provider,
            MacroObservation.series_code == series_code,
            MacroObservation.market_session == "kr_close",
            MacroObservation.retrieved_at < day_start,
        )
        .order_by(MacroObservation.retrieved_at.desc())
    ).first()


def _persist_close_observation(
    session: Session,
    provider: str,
    observation: CollectedObservation,
    run_date: date,
    as_of: datetime,
) -> MacroObservation:
    key_source = f"{provider}|{observation.series_code}|kr_close|{run_date.isoformat()}"
    dedupe_key = hashlib.sha256(key_source.encode()).hexdigest()
    row = session.exec(
        select(MacroObservation).where(MacroObservation.dedupe_key == dedupe_key)
    ).first()
    previous = previous_kr_close_observation(
        session, provider, observation.series_code, run_date
    )
    change_value = observation.value - previous.value if previous is not None else None
    change_pct = (
        change_value / previous.value * 100
        if change_value is not None and previous is not None and previous.value != 0
        else None
    )
    source_date = observation.observed_at.astimezone(KST).date()
    values = {
        "series_code": observation.series_code,
        "category": observation.category,
        "provider": provider,
        "observed_at": observation.observed_at,
        "market_session": "kr_close",
        "value": observation.value,
        "unit": observation.unit,
        "frequency": observation.frequency,
        "previous_value": previous.value if previous is not None else None,
        "change_value": change_value,
        "change_pct": change_pct,
        "source_url": observation.source_url,
        "retrieved_at": as_of,
        "vintage_at": as_of,
        "quality_status": "fresh" if source_date == run_date else "stale",
        "raw_payload": json.dumps(observation.raw_payload, ensure_ascii=False),
    }
    if row is None:
        row = MacroObservation(dedupe_key=dedupe_key, **values)
    else:
        for field, value in values.items():
            setattr(row, field, value)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _current_close_observations(
    session: Session,
    provider: str,
    run_date: date,
) -> list[MacroObservation]:
    day_start = datetime.combine(run_date, time.min, tzinfo=KST).astimezone(timezone.utc)
    next_day = datetime.combine(
        run_date + timedelta(days=1), time.min, tzinfo=KST
    ).astimezone(timezone.utc)
    rows = session.exec(
        select(MacroObservation)
        .where(
            MacroObservation.provider == provider,
            MacroObservation.series_code.in_(FX_SERIES),
            MacroObservation.market_session == "kr_close",
            MacroObservation.retrieved_at >= day_start,
            MacroObservation.retrieved_at < next_day,
        )
        .order_by(MacroObservation.retrieved_at.desc())
    ).all()
    by_series: dict[str, MacroObservation] = {}
    for row in rows:
        by_series.setdefault(row.series_code, row)
    return [by_series[series_code] for series_code in FX_SERIES if series_code in by_series]


def _briefing_values(
    session: Session,
    run_date: date,
    as_of: datetime,
    observations: list[MacroObservation],
    warnings: list[str],
) -> dict[str, object]:
    by_series = {item.series_code: item for item in observations}
    fx: list[dict[str, object]] = []
    for series_code in FX_SERIES:
        row = by_series.get(series_code)
        if row is None:
            continue
        previous = previous_kr_close_observation(
            session, row.provider, series_code, run_date
        )
        raw_payload = json.loads(row.raw_payload)
        fx.append(
            {
            "series_code": series_code,
            "value": row.value,
            "previous_value": row.previous_value,
            "change_value": row.change_value,
            "change_pct": row.change_pct,
            "as_of": row.observed_at.isoformat(),
            "comparison_date": _as_utc(previous.retrieved_at)
            .astimezone(KST)
            .date()
            .isoformat()
            if previous is not None
            else None,
            "quality_status": row.quality_status,
            "provider_last_refreshed": raw_payload.get("provider_last_refreshed"),
            "provider_timezone": raw_payload.get("provider_timezone"),
            "retrieved_at": row.retrieved_at.isoformat(),
                }
        )
    return {
        "as_of": as_of,
        "headline": "한국 장마감 환율 점검",
        "market_summary": json.dumps({"fx": fx}, ensure_ascii=False),
        "regime_summary": "{}",
        "today_calendar": "[]",
        "macro_theses": "[]",
        "ticker_impacts": "[]",
        "data_quality": json.dumps(
            [{"warning": warning} for warning in warnings]
            + [
                {
                    "series_code": item.series_code,
                    "quality_status": item.quality_status,
                    "observed_at": item.observed_at.isoformat(),
                }
                for item in observations
                if item.quality_status != "fresh"
            ],
            ensure_ascii=False,
        ),
        "kakao_text": f"[한국 시장환경 점검] {run_date} 환율",
        "status": "ready" if len(observations) == len(FX_SERIES) else "partial",
        "market_session": "kr_close",
        "assessment_state": "final",
    }


async def run_kr_close_market_briefing(
    session: Session,
    run_date: date,
    *,
    as_of: datetime | None = None,
    provider: AlphaVantageKrCloseFxProvider | None = None,
    force: bool = False,
    queue_notifications: bool = True,
    dispatch_notifications: bool = True,
) -> KrCloseBriefingRunResult:
    as_of = as_of or datetime.now(timezone.utc)
    existing = session.exec(
        select(MacroBriefing).where(
            MacroBriefing.briefing_date == run_date,
            MacroBriefing.briefing_type == "kr_close",
        )
    ).first()
    previous_status = existing.status if existing is not None else None
    if existing is not None and existing.status == "ready" and not force:
        delivery = queue_macro_notification(session, existing) if queue_notifications else None
        session.commit()
        if dispatch_notifications and delivery is not None and delivery.id is not None:
            await dispatch_pending_notifications(session, delivery_ids={delivery.id})
        return KrCloseBriefingRunResult(
            run_date, "already_completed", "reuse", 0, [], existing
        )

    selected_provider = provider or AlphaVantageKrCloseFxProvider()
    try:
        collected = await selected_provider.collect(as_of)
    except Exception as exc:  # noqa: BLE001
        collected_observations: list[CollectedObservation] = []
        warnings = [f"provider_failed:{type(exc).__name__}"]
        provider_name = selected_provider.name
    else:
        collected_observations = collected.observations
        warnings = list(collected.warnings)
        provider_name = collected.provider
    for item in collected_observations:
        if item.series_code in FX_SERIES:
            _persist_close_observation(session, provider_name, item, run_date, as_of)
    observations = _current_close_observations(session, provider_name, run_date)
    available_series = {item.series_code for item in observations}
    missing = [series_code for series_code in FX_SERIES if series_code not in available_series]
    warnings.extend(f"{series_code}:unavailable" for series_code in missing)

    values = _briefing_values(session, run_date, as_of, observations, warnings)
    if existing is None:
        existing = MacroBriefing(
            briefing_date=run_date,
            briefing_type="kr_close",
            dedupe_key=f"macro:{run_date}:kr_close",
            **values,
        )
    else:
        for field, value in values.items():
            setattr(existing, field, value)
    session.add(existing)
    session.commit()
    session.refresh(existing)
    recovered_after_partial = previous_status not in {None, "ready"} and existing.status == "ready"
    delivery = (
        queue_macro_notification(
            session,
            existing,
            requeue_sent=recovered_after_partial,
        )
        if queue_notifications
        else None
    )
    session.commit()
    if dispatch_notifications and delivery is not None and delivery.id is not None:
        await dispatch_pending_notifications(session, delivery_ids={delivery.id})
    return KrCloseBriefingRunResult(
        run_date,
        existing.status,
        "fresh",
        len(observations),
        warnings,
        existing,
    )
