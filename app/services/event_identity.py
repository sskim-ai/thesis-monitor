import hashlib
import json
import re

from app.models.event import Event


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", " ", value.lower()).strip()


def _event_identifier(event: Event) -> str:
    try:
        facts = json.loads(event.confirmed_facts)
    except json.JSONDecodeError:
        facts = []
    if isinstance(facts, list):
        for fact in facts:
            text = str(fact)
            if "receipt number:" in text.lower():
                return text.split(":", 1)[-1].strip()
            if "accession number:" in text.lower():
                return text.split(":", 1)[-1].strip()
    if event.url:
        return event.url.strip().lower()
    return _normalized(event.title)


def event_fingerprint(event: Event) -> str:
    """Stable identity used to prevent evidence reuse across assessments."""
    parts = (
        event.ticker.upper(),
        event.date.isoformat(),
        event.event_type,
        (event.provider or event.source).lower(),
        _event_identifier(event),
    )
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
