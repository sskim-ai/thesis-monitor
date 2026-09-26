"""Opt-in event wire/cache ownership. No database writes or provider fallback."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import codecs
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import httpx
from pydantic import TypeAdapter

from app.providers.base import NewsProvider
from app.services.event_identity import attribute_claim_actor, validate_source_document_identity
from app.services.event_relevance_service import EventRelevanceService, extract_structured_flags
from app.services.unified_run_artifacts import SECRET_KEY, SECRET_VALUE, durable_bytes, durable_json
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_observer import _secret_field, capture_source_response
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_source_replay import read_bound_artifact


HOSTS = {
    "google_news_rss": {"news.google.com"}, "naver_news": {"openapi.naver.com"},
    "sec_edgar": {"www.sec.gov", "data.sec.gov"},
    "opendart": {"opendart.fss.or.kr", "dart.fss.or.kr"},
}
PATHS = {"news.google.com": {"/rss/search"}, "openapi.naver.com": {"/v1/search/news.json"},
    "www.sec.gov": {"/files/company_tickers.json"},
    "dart.fss.or.kr": {"/dsaf001/main.do", "/report/viewer.do"},
    "opendart.fss.or.kr": {"/api/" + name + ".json" for name in (
        "list", "fnlttSinglAcnt", "fnlttSinglAcntAll", "stockTotqySttus", "tsstkDpDecsn",
        "singleSaleSupplyContract", "piicDecsn", "cvbdIsDecsn", "alotMatter")}}


@dataclass(frozen=True)
class CachedEventRead:
    root: Path
    receipt: str
    receipt_sha256: str


def qualify_event_rows(session, rows, target, *, provider, cutoff, lookback_days):
    """Same identity/relevance path for wire capture and byte-owned offline replay."""
    normalized, rejected, candidates = [], [], []
    with session.no_autoflush:
        for raw in rows:
            record = TypeAdapter(dict).dump_python(asdict(raw), mode="json")
            audit = {"raw_event": record, "raw_event_sha256": digest(record),
                     "temporal_identity": "FAIL", "document_identity": "NOT_REACHED",
                     "relevance": "NOT_REACHED"}
            candidates.append(audit)
            if raw.provider != provider or raw.ticker != target.ticker or not (
                cutoff.date() - timedelta(days=lookback_days) <= raw.date <= cutoff.date()
            ):
                rejected.append({"raw_event_sha256": digest(record), "reason": "subject_or_publication_mismatch"})
                continue
            audit["temporal_identity"] = "PASS"
            document_ok = validate_source_document_identity(raw)
            verdict = EventRelevanceService().validate(session, raw, target)
            audit.update(document_identity=raw.document_identity_status, relevance=asdict(verdict))
            if not document_ok or not verdict.accepted:
                rejected.append({"event_url_sha256": digest(raw.url),
                                 "reason": verdict.reason or "document_identity_invalid"})
                continue
            raw.identity_validated, raw.identity_status = True, verdict.status
            raw.subject_company_name, raw.relevance_evidence = verdict.subject_company_id, verdict.evidence
            raw.claim_actor, raw.claim_actor_type = attribute_claim_actor(raw)
            extract_structured_flags(raw)
            normalized.append(raw)
    return normalized, rejected, candidates


class EventReceiptTransport(httpx.AsyncBaseTransport):
    """Bound HTTP transport; original cache receipt bytes remain separate."""

    def __init__(self, *, root: Path, run_id: str, acquisition_id: str, provider: str,
                 policy: UnifiedSourcePolicy, max_requests: int,
                 inner: httpx.AsyncBaseTransport | None,
                 cache: tuple[CachedEventRead, ...] = ()):
        policy.require(provider)
        if provider not in HOSTS or not run_id or not acquisition_id or max_requests < 1:
            raise ValueError("event_owner_plan_invalid")
        if root.exists() or any(p.is_symlink() for p in (root, *root.parents)):
            raise ValueError("new_event_acquisition_root_required")
        if (inner is None) == (not cache):
            raise ValueError("exactly_one_event_wire_or_cache_source_required")
        self.root, self.provider, self.policy = root, provider, policy
        self.run_id, self.acquisition_id = run_id, acquisition_id
        self.inner, self.cache, self.max_requests = inner, cache, max_requests
        self.ordinal, self.used = 0, False
        self.cutoff: datetime | None = None
        self.children: list[dict] = []
        durable_json(root / "plan.json", {**self.identity, "max_requests": max_requests,
            "hosts": sorted(HOSTS[provider]), "mode": "CACHE" if cache else "WIRE",
            "cache_receipt_sha256": [c.receipt_sha256 for c in cache]}, exclusive=True)

    @property
    def identity(self):
        return {"run_id": self.run_id, "acquisition_id": self.acquisition_id,
                "acquisition_class": "RUN_FRESH_ONCE", "role": "news_and_filing_events",
                "provider": self.provider}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        try:
            return await self._handle_async_request(request)
        except (httpx.HTTPError, ValueError, KeyError, LookupError, OSError) as exc:
            self.record_cache_denial(type(exc).__name__)
            raise

    async def _handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.policy.require(self.provider)
        if self.used or request.method != "GET" or request.url.scheme != "https" or (
            request.url.host not in HOSTS[self.provider] or request.url.userinfo
        ):
            raise ValueError("event_request_not_authorized")
        path = request.url.path
        sec_path = path.removeprefix("/submissions/CIK").removesuffix(".json")
        if not (path in PATHS.get(request.url.host, set()) or (request.url.host == "data.sec.gov"
            and path == f"/submissions/CIK{sec_path}.json" and len(sec_path) == 10 and sec_path.isdigit())):
            raise ValueError("event_request_path_not_authorized")
        if self.ordinal >= self.max_requests:
            raise ValueError("event_request_budget_exhausted")
        self.ordinal += 1
        identity = f"read-{self.ordinal:04d}"
        params = [[k, v] for k, v in request.url.params.multi_items()
                  if k != "crtfc_key" and not SECRET_KEY.search(k)]
        safe_request = {"method": "GET", "route": str(request.url.copy_with(query=None)),
                        "params": params}
        receipt = {**self.identity, "ordinal": self.ordinal,
            "request": safe_request, "request_sha256": digest(safe_request),
            "requested_at": datetime.now(timezone.utc).isoformat()}
        if self.cache:
            durable_json(self.root / f"{identity}.intent.json", receipt, exclusive=True)
            if self.ordinal > len(self.cache):
                raise ValueError("event_cache_read_set_exhausted")
            cached = self.cache[self.ordinal - 1]
            original_bytes = read_bound_artifact(cached.root, cached.receipt, cached.receipt_sha256)
            original = json.loads(original_bytes)
            self.policy.require(original.get("provider"))
            if original.get("provider") != self.provider or original.get("request") != safe_request:
                raise ValueError("event_cache_identity_mismatch")
            if original.get("outcome") != "HTTP_RESPONSE" or not 200 <= original.get("http_status", 0) < 300:
                raise ValueError("event_cache_successful_original_required")
            if original.get("request_sha256") != digest(safe_request):
                raise ValueError("event_cache_request_hash_mismatch")
            stamps = [datetime.fromisoformat(original[k]) for k in ("requested_at", "received_at")]
            for stamp in stamps:
                if stamp.utcoffset() is None or self.cutoff is None or stamp > self.cutoff:
                    raise ValueError("event_cache_original_time_invalid")
            if stamps[0] > stamps[1]:
                raise ValueError("event_cache_original_time_invalid")
            encoding = original.get("response_encoding")
            if not isinstance(encoding, str):
                raise ValueError("event_cache_decode_identity_missing")
            codecs.lookup(encoding)
            raw = read_bound_artifact(cached.root, original["artifact"], original["artifact_sha256"])
            try:
                secret_field = _secret_field(json.loads(raw))
            except ValueError:
                secret_field = False
            if SECRET_VALUE.search(raw.decode("utf-8", errors="replace")) or secret_field:
                raise ValueError("event_cache_secret_risk")
            durable_bytes(self.root / f"{identity}.original.json", original_bytes, exclusive=True)
            durable_bytes(self.root / f"{identity}.body", raw, exclusive=True)
            receipt.update(outcome="CACHE_SOURCE_OPEN", received_at=datetime.now(timezone.utc).isoformat(),
                artifact=f"{identity}.body", artifact_sha256=hashlib.sha256(raw).hexdigest(),
                original_receipt=f"{identity}.original.json", original_receipt_sha256=cached.receipt_sha256,
                original_requested_at=original["requested_at"], original_received_at=original["received_at"],
                response_encoding=encoding)
            durable_json(self.root / f"{identity}.response.json", receipt, exclusive=True)
            response = httpx.Response(original["http_status"], content=raw, request=request)
            response.encoding = encoding
        else:
            async def send():
                response = await self.inner.handle_async_request(request)
                await response.aread()
                receipt["response_encoding"] = codecs.lookup(response.encoding).name
                return response
            try:
                response = await capture_source_response(root=self.root, identity=identity,
                                                         receipt=receipt, send=send)
            finally:
                path = self.root / f"{identity}.response.json"
                self.children.append({"receipt": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            return response
        path = self.root / f"{identity}.response.json"
        self.children.append({"receipt": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        return response

    async def aclose(self):
        # Provider clients may be reopened for the bounded collection retry.
        pass

    def record_cache_denial(self, error_type: str):
        identity = f"read-{self.ordinal:04d}"
        path = self.root / f"{identity}.response.json"
        intent = self.root / f"{identity}.intent.json"
        if self.cache and intent.exists() and not path.exists():
            receipt = json.loads(intent.read_bytes())
            receipt.update(outcome="CACHE_DENIED", error_type=error_type,
                received_at=datetime.now(timezone.utc).isoformat(), artifact=None, artifact_sha256=None)
            durable_json(path, receipt, exclusive=True)
            self.children.append({"receipt": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})

    async def close_owner(self):
        if self.inner is not None:
            await self.inner.aclose()


class EventAcquisition:
    def __init__(self, transport: EventReceiptTransport, *, cutoff: datetime, max_attempts: int = 1):
        if cutoff.utcoffset() is None or not 1 <= max_attempts <= 10:
            raise ValueError("event_cutoff_and_budget_required")
        self.transport, self.cutoff, self.max_attempts = transport, cutoff, max_attempts
        self.transport.cutoff = cutoff
        self._used = False

    async def collect(self, session, provider, target, *, lookback_days: int, aliases: list[str]):
        from app.providers.filings import OpenDARTProvider, SecEdgarProvider
        from app.providers.news import GoogleNewsRSSProvider, NaverNewsProvider
        from app.services.collection_service import _raw_event_to_model
        classes = {c.name: c for c in (GoogleNewsRSSProvider, NaverNewsProvider, SecEdgarProvider, OpenDARTProvider)}
        if self._used or type(provider) is not classes.get(self.transport.provider):
            raise ValueError("event_owner_identity_or_reuse_mismatch")
        if session.new or session.dirty or session.deleted or target.id is None:
            raise ValueError("event_clean_persisted_identity_required")
        if lookback_days < 1:
            raise ValueError("event_lookback_required")
        self.transport.policy.require(target.identity_provider)
        self._used = True
        provider.transport, provider.as_of = self.transport, self.cutoff.date()
        if isinstance(provider, OpenDARTProvider):
            provider.unified_corp_code = target.corp_code
        if isinstance(provider, SecEdgarProvider):
            if not target.cik:
                raise ValueError("unified_sec_issuer_identity_missing")
            provider.unified_cik = target.cik
        normalized, attempts, rejected, candidates = [], [], [], []
        try:
            for attempt in range(1, self.max_attempts + 1):
                try:
                    rows = await provider.fetch_events(target.ticker, lookback_days,
                        **({"search_aliases": aliases} if isinstance(provider, NewsProvider) else {}))
                except (httpx.HTTPError, ValueError, KeyError, LookupError, OSError) as exc:
                    self.transport.record_cache_denial(type(exc).__name__)
                    attempts.append({"attempt": attempt, "error_type": type(exc).__name__})
                    continue
                attempts.append({"attempt": attempt, "raw_event_count": len(rows)})
                normalized, rejected, candidates = qualify_event_rows(session, rows, target,
                    provider=self.transport.provider, cutoff=self.cutoff, lookback_days=lookback_days)
                break
        finally:
            self.transport.used = True
            await self.transport.close_owner()
        values = [_raw_event_to_model(r).model_dump(mode="json", exclude={"id", "created_at"}) for r in normalized]
        # Preserve exact owner defaults separately; no event row is inserted.
        value = {**self.transport.identity, "ticker": target.ticker,
            "security_record_id": target.id, "security_record_sha256": digest(target.model_dump(mode="json")),
            "cutoff": self.cutoff.isoformat(), "lookback_days": lookback_days,
            "children": self.transport.children, "attempts": attempts, "rejected": rejected,
            "candidates": candidates,
            "normalized": values, "normalized_sha256": digest(values),
            "denial": None if values else "optional_event_unavailable",
            "owner_contracts": ["event_identity", "event_relevance", "event_financial_validation"],
            "owner_fingerprints": {name: hashlib.sha256((Path(__file__).parents[2] / name).read_bytes()).hexdigest()
                for name in ("app/services/unified_event_acquisition.py", "app/providers/news.py",
                    "app/providers/filings.py", "app/services/event_identity.py",
                    "app/services/event_relevance_service.py", "app/services/collection_service.py",
                    "app/services/financial_validation.py")}}
        if self.transport.cache and self.transport.ordinal != len(self.transport.cache):
            raise ValueError("event_cache_unexpected_child")
        durable_json(self.transport.root / "normalization.json", value, exclusive=True)
        return normalized
