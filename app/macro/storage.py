import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.macro.providers.base import CollectedEvent, CollectedObservation, MacroProvider
from app.models.macro import MacroEvent, MacroObservation


def _dedupe_key(provider: str, observation: CollectedObservation) -> str:
    source = f"{provider}|{observation.series_code}|{observation.observed_at.isoformat()}"
    return hashlib.sha256(source.encode()).hexdigest()


def _freshness_status(observation: CollectedObservation, as_of: datetime) -> str:
    age = as_of.astimezone(timezone.utc) - observation.observed_at.astimezone(timezone.utc)
    limits = {
        "d": timedelta(days=4),
        "daily": timedelta(days=4),
        "w": timedelta(days=10),
        "weekly": timedelta(days=10),
        "m": timedelta(days=45),
        "monthly": timedelta(days=45),
        "q": timedelta(days=120),
        "quarterly": timedelta(days=120),
        "a": timedelta(days=400),
        "annual": timedelta(days=400),
    }
    limit = limits.get((observation.frequency or "").lower(), timedelta(days=7))
    return "stale" if age > limit else "fresh"


def _previous_observation(
    session: Session,
    provider: str,
    observation: CollectedObservation,
) -> MacroObservation | None:
    return session.exec(
        select(MacroObservation)
        .where(
            MacroObservation.provider == provider,
            MacroObservation.series_code == observation.series_code,
            MacroObservation.observed_at < observation.observed_at,
        )
        .order_by(MacroObservation.observed_at.desc())
    ).first()


def persist_observation(
    session: Session,
    provider: str,
    observation: CollectedObservation,
    as_of: datetime,
) -> tuple[MacroObservation, bool]:
    dedupe_key = _dedupe_key(provider, observation)
    existing = session.exec(
        select(MacroObservation).where(MacroObservation.dedupe_key == dedupe_key)
    ).first()
    if existing is not None:
        return existing, False

    previous = _previous_observation(session, provider, observation)
    change_value = observation.value - previous.value if previous is not None else None
    change_pct = None
    if change_value is not None and previous is not None and previous.value != 0:
        change_pct = round(change_value / abs(previous.value) * 100, 4)
    row = MacroObservation(
        dedupe_key=dedupe_key,
        series_code=observation.series_code,
        category=observation.category,
        provider=provider,
        observed_at=observation.observed_at,
        market_session=observation.market_session,
        value=observation.value,
        unit=observation.unit,
        frequency=observation.frequency,
        previous_value=previous.value if previous is not None else None,
        change_value=change_value,
        change_pct=change_pct,
        source_url=observation.source_url,
        vintage_at=as_of,
        is_preliminary=observation.is_preliminary,
        is_revised=observation.is_revised,
        quality_status=_freshness_status(observation, as_of),
        raw_payload=json.dumps(observation.raw_payload, ensure_ascii=False),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row, True


def persist_event(session: Session, provider: str, event: CollectedEvent) -> tuple[MacroEvent, bool]:
    existing = session.exec(
        select(MacroEvent).where(MacroEvent.event_key == event.event_key)
    ).first()
    surprise_value = None
    if event.actual is not None and event.consensus is not None:
        surprise_value = event.actual - event.consensus
    values = {
        "event_type": event.event_type,
        "category": event.category,
        "title": event.title,
        "country": event.country,
        "region": event.region,
        "scheduled_at": event.scheduled_at,
        "released_at": event.released_at,
        "event_status": event.event_status,
        "actual": event.actual,
        "consensus": event.consensus,
        "previous": event.previous,
        "revised_previous": event.revised_previous,
        "unit": event.unit,
        "surprise_value": surprise_value,
        "impact_level": event.impact_level,
        "confirmed_facts": json.dumps(event.confirmed_facts, ensure_ascii=False),
        "inferred_implications": json.dumps(event.inferred_implications, ensure_ascii=False),
        "unknowns": json.dumps(event.unknowns, ensure_ascii=False),
        "provider": provider,
        "source_url": event.source_url,
        "source_reliability": event.source_reliability,
        "retrieved_at": datetime.now(timezone.utc),
    }
    if existing is not None:
        for key, value in values.items():
            setattr(existing, key, value)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing, False

    row = MacroEvent(event_key=event.event_key, **values)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row, True


async def collect_macro_data(
    session: Session,
    providers: list[MacroProvider],
    as_of: datetime,
) -> tuple[int, int, list[str]]:
    observation_count = 0
    event_count = 0
    warnings: list[str] = []
    for provider in providers:
        try:
            result = await provider.collect(as_of)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{provider.name}: {type(exc).__name__}")
            continue
        warnings.extend(f"{provider.name}: {warning}" for warning in result.warnings)
        for observation in result.observations:
            _, created = persist_observation(session, provider.name, observation, as_of)
            observation_count += int(created)
        for event in result.events:
            _, created = persist_event(session, provider.name, event)
            event_count += int(created)
    return observation_count, event_count, warnings
