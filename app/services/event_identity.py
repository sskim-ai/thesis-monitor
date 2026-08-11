import hashlib
import json
import re
from urllib.parse import parse_qs, urlparse

from app.models.event import Event
from app.providers.base import RawEvent


_BROKERAGE_TERMS = (
    "증권",
    "證",
    "목표가",
    "목표주가",
    "brokerage",
    "analyst",
    "price target",
    "target price",
    "jpmorgan",
    "jp모건",
    "morgan stanley",
    "goldman sachs",
    "ubs",
)


def source_document_id_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    receipt = query.get("rcpNo") or query.get("rcpno")
    if receipt and receipt[0]:
        return receipt[0]
    accession = re.search(r"/(\d{10}-\d{2}-\d{6})/", url)
    return accession.group(1) if accession else None


def source_document_id_from_facts(facts: list[str]) -> str | None:
    for fact in facts:
        match = re.search(
            r"(?:receipt|accession) (?:number|id):\s*([0-9-]+)",
            fact,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(1)
    return None


def validate_source_document_identity(raw_event: RawEvent) -> bool:
    url_id = source_document_id_from_url(raw_event.url)
    fact_id = source_document_id_from_facts(raw_event.confirmed_facts)
    supplied_id = raw_event.source_document_id
    identifiers = [item for item in (url_id, fact_id, supplied_id) if item]
    if not identifiers:
        raw_event.document_identity_status = "not_applicable"
        return True
    if len(set(identifiers)) != 1:
        raw_event.document_identity_status = "invalid_mismatch"
        raw_event.rejected_reason = "source_document_identity_mismatch"
        raw_event.unknowns.append(
            "공시 URL과 저장된 문서 식별자가 일치하지 않아 투자 판단에서 제외했습니다."
        )
        return False
    raw_event.source_document_id = identifiers[0]
    raw_event.document_identity_status = "validated"
    return True


def attribute_claim_actor(raw_event: RawEvent) -> tuple[str | None, str]:
    if raw_event.provider == "opendart":
        return raw_event.company_name, "company_official_filing"
    if raw_event.provider == "sec_edgar":
        return raw_event.company_name, "company_official_filing"
    if raw_event.provider == "company_ir":
        return raw_event.company_name, "company_management"
    text = f"{raw_event.title} {raw_event.summary}".lower()
    matched = next((term for term in _BROKERAGE_TERMS if term.lower() in text), None)
    if matched:
        return matched, "brokerage"
    issuer_terms = [
        term.lower().strip()
        for term in (raw_event.company_name, raw_event.ticker)
        if term and len(term.strip()) >= 2
    ]
    direct_company_claim = any(
        re.search(
            rf"{re.escape(term)}.{{0,80}}(?:lowered|raised|updated|issued|announced|"
            r"guidance|forecast|outlook|가이던스|전망|상향|하향|발표)",
            text,
        )
        for term in issuer_terms
    )
    if direct_company_claim:
        return raw_event.company_name or raw_event.ticker, "company_management"
    if any(term in text for term in ("정부", "ministry", "regulator", "연준", "fed ")):
        return None, "government"
    return None, "media"


def event_has_valid_document_identity(event: Event) -> bool:
    return event.document_identity_status not in {"invalid_mismatch", "invalid"}


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", " ", value.lower()).strip()


def _event_identifier(event: Event) -> str:
    if event.source_document_id:
        return event.source_document_id
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
