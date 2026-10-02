"""Bounded news plan and source-byte replay for opt-in stock materialization."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
from typing import Literal
from xml.etree import ElementTree

import httpx
from pydantic import Field, model_validator
from sqlmodel import Session, SQLModel, create_engine

from app.models.security import SecurityMaster
from app.providers.news import GoogleNewsRSSProvider, NaverNewsProvider, clean_text, serialize_news_request
from app.services.collection_service import _raw_event_to_model
from app.services.event_identity import event_fingerprint, event_is_eligible_for_current_analysis
from app.services.news_query_service import NewsQueryService
from app.services.thesis_evaluation_service import _baseline_evidence
from app.services.unified_event_acquisition import EventReceiptTransport, qualify_event_rows
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import ContractModel, digest


PROVIDERS = {"us": GoogleNewsRSSProvider, "kr": NaverNewsProvider}
OWNER_FILES = ("app/services/unified_stock_event_input.py", "app/services/unified_event_acquisition.py",
    "app/providers/news.py", "app/services/news_query_service.py", "app/services/security_master_service.py",
    "app/services/event_identity.py", "app/services/event_relevance_service.py",
    "app/services/collection_service.py", "app/services/event_classifier.py", "app/services/event_interpreter.py",
    "app/services/thesis_scoring.py", "app/services/thesis_evaluation_service.py",
    "app/services/financial_validation.py")


def fingerprints():
    root = Path(__file__).resolve().parents[2]
    return {name: sha256_bytes((root / name).read_bytes()) for name in OWNER_FILES}


def request_identity(request):
    return {"method": request.method, "route": str(request.url.copy_with(query=None)),
            "params": [[k, v] for k, v in request.url.params.multi_items()]}


class NewsRead(ContractModel):
    subject: str
    market: Literal["us", "kr"]
    provider: Literal["google_news_rss", "naver_news"]
    provider_owner: str
    source_receipt_owner: Literal["PlannedNewsTransport/EventReceiptTransport"] = "PlannedNewsTransport/EventReceiptTransport"
    validation_path: Literal["source_bytes -> existing_parser -> identity -> relevance -> temporal -> business_review -> canonical_event -> typed_union"] = "source_bytes -> existing_parser -> identity -> relevance -> temporal -> business_review -> canonical_event -> typed_union"
    run_id: str
    acquisition_id: str
    security: dict
    aliases: tuple[str, ...]
    lookback_days: int = Field(ge=1)
    request: dict
    request_sha256: str
    owner_fingerprints: dict
    security_universe_sha256: str
    max_requests: Literal[1] = 1
    max_attempts: Literal[1] = 1
    retries: Literal[0] = 0
    redirects: Literal[False] = False

    @model_validator(mode="after")
    def exact_query(self):
        target = SecurityMaster.model_validate(self.security)
        if (self.provider != PROVIDERS[self.market].name or target.ticker != self.subject
                or self.provider_owner != PROVIDERS[self.market].__module__ + "." + PROVIDERS[self.market].__name__):
            raise ValueError("news_subject_provider_mismatch")
        if not target.id or not target.canonical_security_id or not target.canonical_company_id:
            raise ValueError("news_canonical_identity_required")
        aliases = NewsQueryService().aliases(target)
        if tuple(aliases) != self.aliases:
            raise ValueError("news_alias_owner_mismatch")
        provider = PROVIDERS[self.market]()
        request = (httpx.Request("GET", provider.request_url(target.ticker, self.lookback_days,
                       search_aliases=aliases)) if self.market == "us" else
                   httpx.Request("GET", provider.endpoint, params=provider.request_params(target.ticker,
                       search_aliases=aliases)))
        if self.request != request_identity(request) or self.request_sha256 != digest(self.request):
            raise ValueError("news_frozen_query_mismatch")
        if self.owner_fingerprints != fingerprints():
            raise ValueError("news_owner_code_changed")
        return self


def make_read(*, security, market, run_id, lookback_days, security_records):
    target = SecurityMaster.model_validate(security)
    aliases = NewsQueryService().aliases(target)
    provider = PROVIDERS[market]()
    request = (httpx.Request("GET", provider.request_url(target.ticker, lookback_days, search_aliases=aliases))
        if market == "us" else httpx.Request("GET", provider.endpoint,
            params=provider.request_params(target.ticker, search_aliases=aliases)))
    identity = request_identity(request)
    return NewsRead(subject=target.ticker, market=market, provider=provider.name, run_id=run_id,
        provider_owner=type(provider).__module__ + "." + type(provider).__name__,
        acquisition_id=run_id + ":" + target.ticker, security=target.model_dump(mode="json"),
        aliases=tuple(aliases), lookback_days=lookback_days, request=identity,
        request_sha256=digest(identity), owner_fingerprints=fingerprints(),
        security_universe_sha256=digest(security_records))


class PlannedNewsTransport(EventReceiptTransport):
    def __init__(self, *, read: NewsRead, root, policy, inner, settings_identity=None):
        self.read = NewsRead.model_validate(read.model_dump(mode="json"))
        self.settings_identity = settings_identity
        super().__init__(root=root, run_id=read.run_id, acquisition_id=read.acquisition_id,
            provider=read.provider, policy=policy, max_requests=1, inner=inner)

    async def _handle_async_request(self, request):
        if self.read.market == "kr" and self.settings_identity is not None:
            credentials = [request.headers.get("X-Naver-Client-Id"),
                           request.headers.get("X-Naver-Client-Secret")]
            if not all(credentials) or digest(credentials) != self.settings_identity:
                self.record_pre_dispatch_denial("naver_settings_identity_mismatch", "settings")
                raise ValueError("naver_settings_identity_mismatch")
        expected = serialize_news_request(self.read.request["method"],
            self.read.request["route"], self.read.request["params"])
        if request_identity(request) != self.read.request or request.url != expected.url:
            self.record_pre_dispatch_denial("news_request_outside_frozen_plan", "wire")
            raise ValueError("news_request_outside_frozen_plan")
        return await super()._handle_async_request(request)


class BoundNewsInput(ContractModel):
    read: NewsRead
    security_records: tuple[dict, ...]
    response_receipt_b64: str
    normalization_b64: str
    raw_response_b64: str | None = None


def _decode(value):
    return base64.b64decode(value, validate=True)


def _publication_records(response, market, source_url):
    if market == "us":
        return [{"title": clean_text(n.findtext("title")) or "Untitled news item",
                 "url": n.findtext("link") or source_url, "published": n.findtext("pubDate")}
                for n in ElementTree.fromstring(response.text).findall(".//item")]
    return [{"title": clean_text(n.get("title")) or "Untitled Naver news item",
             "url": n.get("originallink") or n.get("link") or NaverNewsProvider.endpoint,
             "published": n.get("pubDate")} for n in response.json().get("items", [])]


def replay_news(source: BoundNewsInput, *, security: dict, business_cutoff: datetime, policy,
                source_query_cutoff: datetime | None = None):
    """No network/files/database side effects; all source inputs are explicit."""
    source = BoundNewsInput.model_validate(source.model_dump(mode="json"))
    read = source.read
    if business_cutoff.utcoffset() is None:
        raise ValueError("aware_business_cutoff_required")
    query_cutoff = source_query_cutoff or business_cutoff
    if query_cutoff.utcoffset() is None or query_cutoff > business_cutoff:
        raise ValueError('source_query_cutoff_after_availability')
    policy.require(read.provider)
    policy.require(security["identity_provider"])
    if SecurityMaster.model_validate(security).model_dump(mode="json") != read.security:
        raise ValueError("news_stock_identity_mismatch")
    if digest(list(source.security_records)) != read.security_universe_sha256:
        raise ValueError("news_security_universe_mismatch")
    targets = [r for r in source.security_records if r["ticker"] == read.subject]
    if targets != [read.security]:
        raise ValueError("news_subject_missing_or_duplicate")
    receipt_bytes, norm_bytes = _decode(source.response_receipt_b64), _decode(source.normalization_b64)
    receipt, norm = json.loads(receipt_bytes), json.loads(norm_bytes)
    for row in (receipt, norm):
        if (row.get("run_id"), row.get("acquisition_id"), row.get("provider")) != (
            read.run_id, read.acquisition_id, read.provider):
            raise ValueError("news_acquisition_identity_mismatch")
    if receipt.get("ordinal") != 1 or receipt.get("request") != read.request or receipt.get("request_sha256") != read.request_sha256:
        raise ValueError("news_request_receipt_mismatch")
    start, end = [datetime.fromisoformat(receipt[k]) for k in ("requested_at", "received_at")]
    if any(t.utcoffset() is None for t in (start, end)) or not start <= end <= business_cutoff:
        raise ValueError("news_source_availability_after_business_cutoff")
    if norm.get("security_record_sha256") != digest(read.security) or norm.get("ticker") != read.subject:
        raise ValueError("news_normalization_identity_mismatch")
    norm_cutoff = datetime.fromisoformat(norm["cutoff"])
    if (norm_cutoff.utcoffset() is None or norm_cutoff > query_cutoff
            or norm_cutoff.date() != query_cutoff.date()):
        raise ValueError("news_normalization_cutoff_mismatch")
    if norm.get("lookback_days") != read.lookback_days or len(norm.get("attempts", [])) != 1:
        raise ValueError("news_attempt_or_lookback_mismatch")
    if norm.get("children") != [{"receipt": "read-0001.response.json", "sha256": sha256_bytes(receipt_bytes)}]:
        raise ValueError("news_normalization_source_receipt_mismatch")
    if norm.get("normalized_sha256") != digest(norm.get("normalized")):
        raise ValueError("news_normalization_hash_mismatch")
    binding = {"provider": read.provider, "request_sha256": read.request_sha256,
        "source_receipt_sha256": sha256_bytes(receipt_bytes), "normalization_sha256": sha256_bytes(norm_bytes),
        "raw_sha256": receipt.get("artifact_sha256"), "business_cutoff": business_cutoff.isoformat(),
        "requested_at": start.isoformat(), "received_at": end.isoformat(),
        "candidates": [], "source_items": [], "selected": [], "evidence": []}
    if receipt.get("outcome") != "HTTP_RESPONSE":
        if source.raw_response_b64 is not None or norm.get("normalized"):
            raise ValueError("failed_news_receipt_has_consumed_evidence")
        return {**binding, "denial": "event_owner_error:" + str(receipt.get("outcome"))}
    raw = _decode(source.raw_response_b64) if source.raw_response_b64 is not None else b""
    if sha256_bytes(raw) != receipt.get("artifact_sha256"):
        raise ValueError("news_raw_source_hash_mismatch")
    if not 200 <= receipt.get("http_status", 0) < 300:
        if norm.get("normalized"):
            raise ValueError("http_error_has_normalized_events")
        return {**binding, "denial": "event_owner_error:HTTP_" + str(receipt.get("http_status"))}
    request = httpx.Request("GET", read.request["route"], params=read.request["params"])
    response = httpx.Response(receipt["http_status"], content=raw, request=request)
    response.encoding = receipt["response_encoding"]
    provider = PROVIDERS[read.market](as_of=norm_cutoff.date())
    source_url = (provider.request_url(read.subject, read.lookback_days, search_aliases=list(read.aliases))
                  if read.market == "us" else provider.endpoint)
    try:
        rows = provider.parse_response(response, ticker=read.subject,
            **({"source_url": source_url} if read.market == "us" else {}))
        publication = _publication_records(response, read.market, source_url)
    except (ValueError, ElementTree.ParseError):
        if norm.get("normalized"):
            raise ValueError("malformed_body_has_consumed_evidence") from None
        return {**binding, "denial": "event_owner_error:MALFORMED_BODY"}
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            targets = [SecurityMaster.model_validate(r) for r in source.security_records]
            session.add_all(targets)
            session.commit()
            target = next(r for r in targets if r.ticker == read.subject)
            normalized, rejected, candidates = qualify_event_rows(session, rows, target,
                provider=read.provider, cutoff=norm_cutoff, lookback_days=read.lookback_days)
            events = [_raw_event_to_model(r) for r in normalized]
            values = [e.model_dump(mode="json", exclude={"id", "created_at"}) for e in events]
    finally:
        engine.dispose()
    if values != norm["normalized"] or rejected != norm["rejected"] or candidates != norm.get("candidates"):
        raise ValueError("news_raw_normalization_replay_mismatch")
    binding.update(candidates=candidates, source_items=publication)
    seen, selected = set(), []
    for event in events:
        fp = event_fingerprint(event)
        audit = {"event_fingerprint": fp, "event_type": event.event_type,
            "normalized_event_sha256": digest(event.model_dump(mode="json", exclude={"id", "created_at"})),
            "title": event.title, "url": event.url, "date": str(event.date),
            "relevance_score": event.relevance_score, "requires_review": event.requires_review,
            "status": "DENIED", "reason": None}
        matches = [r for r in publication if (r["title"], r["url"]) == (event.title, event.url)]
        try:
            times = {parsedate_to_datetime(r["published"]) for r in matches}
            if len(times) != 1:
                raise ValueError("ambiguous_publication")
            at = next(iter(times))
            if at.utcoffset() is None or at > query_cutoff:
                raise ValueError("future_or_unverified_publication")
            audit["published_at"] = at.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError, IndexError, StopIteration):
            audit["reason"] = "temporal_failure"
        if audit["reason"] is None:
            if not event_is_eligible_for_current_analysis(event):
                audit["reason"] = "identity_failure"
            elif not event.requires_review or not _baseline_evidence([event]):
                audit["reason"] = "business_relevance_failure"
            elif fp in seen:
                audit["reason"] = "duplicate"
            else:
                audit.update(status="PASS", reason=None)
                selected.append(event)
        seen.add(fp)
        binding["selected"].append(audit)
    binding["evidence"] = _baseline_evidence(selected)
    binding["denial"] = None if selected else "no_qualified_business_event"
    return binding
