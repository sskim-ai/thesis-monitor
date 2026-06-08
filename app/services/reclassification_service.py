import json
from dataclasses import dataclass
from datetime import date

from sqlmodel import Session, select

from app.models.event import Event
from app.providers.base import RawEvent
from app.services.event_classifier import classify_event
from app.services.thesis_scoring import score_event


@dataclass(frozen=True)
class ReclassifyResult:
    scanned_count: int
    changed_count: int
    updated_count: int


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _event_to_raw(event: Event) -> RawEvent:
    return RawEvent(
        ticker=event.ticker,
        company_name=event.company_name,
        date=event.date if isinstance(event.date, date) else date.today(),
        source=event.source,
        provider=event.provider,
        title=event.title,
        url=event.url,
        summary=event.raw_summary or event.title,
        keywords=_json_list(event.keywords),
        confirmed_facts=_json_list(event.confirmed_facts),
        inferred_implications=_json_list(event.inferred_implications),
        unknowns=_json_list(event.unknowns),
    )


def reclassify_events(
    session: Session,
    ticker: str | None = None,
    provider: str | None = None,
    dry_run: bool = True,
) -> ReclassifyResult:
    query = select(Event)
    if ticker:
        query = query.where(Event.ticker == ticker.upper())
    if provider:
        query = query.where(Event.provider == provider)

    events = list(session.exec(query).all())
    changed_count = 0
    updated_count = 0

    for event in events:
        raw = _event_to_raw(event)
        new_type = classify_event(raw)
        new_relevance = score_event(raw, new_type)
        changed = (
            event.event_type != new_type.value
            or event.relevance_score != new_relevance.relevance_score
            or event.requires_review != new_relevance.requires_review
            or event.relevance_reason != new_relevance.reason
        )
        if not changed:
            continue
        changed_count += 1
        if dry_run:
            continue
        event.event_type = new_type.value
        event.relevance_score = new_relevance.relevance_score
        event.requires_review = new_relevance.requires_review
        event.relevance_reason = new_relevance.reason
        updated_count += 1

    if not dry_run:
        session.commit()

    return ReclassifyResult(
        scanned_count=len(events),
        changed_count=changed_count,
        updated_count=updated_count,
    )
