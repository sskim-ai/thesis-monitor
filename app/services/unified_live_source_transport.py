"""Bounded, receipt-first transport for an opt-in source proof worker only."""

from datetime import datetime, timezone
import hashlib
import time

import httpx

from app.services.unified_run_artifacts import durable_bytes, durable_json
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_observer import _secret_field


class SourceSafetyStop(BaseException):
    """Must escape provider catch-and-continue handlers."""


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class BoundedTransport:
    """No implicit HTTP retries, redirects, semantic retries, or secret receipts."""

    def __init__(self, *, root, maximum_logical, guard, secrets=()):
        if type(maximum_logical) is not int or maximum_logical < 1:
            raise ValueError("finite_transport_budget_required")
        self.root, self.maximum_logical, self.guard = root, maximum_logical, guard
        self.secrets = tuple(s for s in secrets if s)
        self.logical = self.attempts = self.retries = 0

    def begin(self, request, *, secret=False):
        self.guard()
        if self.logical >= self.maximum_logical:
            raise SourceSafetyStop("transport_budget_exhausted")
        self.logical += 1
        row = {"logical_ordinal": self.logical, "requested_at": utc_now(),
               "request": None if secret else request,
               "request_sha256": None if secret else digest(request),
               "secret_exchange": secret, "timeout_seconds": 600, "maximum_attempts": 3}
        durable_json(self.root / f"logical-{self.logical:04d}.json", row, exclusive=True)
        return row

    def record(self, row, attempt, response=None, error=None):
        self.attempts += 1
        self.retries += int(attempt > 1)
        receipt = {**row, "attempt": attempt, "received_at": utc_now(),
                   "http_status": response.status_code if response is not None else None,
                   "error_class": type(error).__name__ if error is not None else None,
                   "artifact": None, "source_sha256": None}
        name = f"logical-{row['logical_ordinal']:04d}-attempt-{attempt}"
        if response is not None and row["secret_exchange"]:
            try:
                token = response.json().get("token")
                if token:
                    self.secrets += (token,)
            except (ValueError, AttributeError):
                pass
        elif response is not None:
            raw = response.content
            try:
                field_risk = _secret_field(response.json())
            except ValueError:
                field_risk = False
            if field_risk or any(s.encode() in raw for s in self.secrets):
                receipt["error_class"] = "SECRET_IN_SOURCE_BODY"
                durable_json(self.root / (name + ".json"), receipt, exclusive=True)
                raise SourceSafetyStop("secret_integrity_failure")
            receipt.update(artifact=name + ".body", source_sha256=hashlib.sha256(raw).hexdigest())
            durable_bytes(self.root / receipt["artifact"], raw, exclusive=True)
        durable_json(self.root / (name + ".json"), receipt, exclusive=True)
        if response is not None and response.status_code in {401, 403}:
            raise SourceSafetyStop("provider_authentication_or_authorization_failed")

    def post(self, client, url, *, json, headers, request, secret=False):
        row = self.begin(request, secret=secret)
        frozen = digest({"url": url, "body": json, "headers": headers})
        for attempt in range(1, 4):
            self.guard()
            if frozen != digest({"url": url, "body": json, "headers": headers}):
                raise SourceSafetyStop("retry_request_changed")
            try:
                response = client.post(url, json=json, headers=headers, timeout=600)
            except httpx.TransportError as exc:
                self.record(row, attempt, error=exc)
                if attempt == 3:
                    raise
            else:
                self.record(row, attempt, response=response)
                if response.status_code not in {429, 500, 502, 503, 504} or attempt == 3:
                    return response
            time.sleep(attempt)

    async def send(self, request, transport):
        body = await request.aread()
        secret = request.url.path == "/oauth2/token"
        import json
        payload = json.loads(body) if body else None
        public = {"method": request.method, "route": request.url.path,
                  "query": dict(request.url.params), "body": payload,
                  "api_id": request.headers.get("api-id"),
                  "cursor_sha256": hashlib.sha256(request.headers.get("next-key", "").encode()).hexdigest()}
        row = self.begin(public, secret=secret)
        fingerprint = digest([str(request.url), request.method, body.hex(), dict(request.headers)])
        import asyncio
        for attempt in range(1, 4):
            self.guard()
            if fingerprint != digest([str(request.url), request.method, body.hex(), dict(request.headers)]):
                raise SourceSafetyStop("retry_request_changed")
            request.extensions["timeout"] = {k: 600.0 for k in ("connect", "read", "write", "pool")}
            try:
                response = await transport.handle_async_request(request)
                await response.aread()
            except httpx.TransportError as exc:
                self.record(row, attempt, error=exc)
                if attempt == 3:
                    raise
            else:
                self.record(row, attempt, response=response)
                if response.status_code not in {429, 500, 502, 503, 504} or attempt == 3:
                    return response
                await response.aclose()
            await asyncio.sleep(attempt)

    def counts(self):
        return {"logical": self.logical, "HTTP_attempts": self.attempts, "retries": self.retries,
                "maximum_logical": self.maximum_logical, "maximum_HTTP_attempts": self.maximum_logical * 3}


class LiveAsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self, *, recorder, authorize):
        self.recorder, self.authorize = recorder, authorize
        self.native = httpx.AsyncHTTPTransport(retries=0)

    async def handle_async_request(self, request):
        self.authorize(request)
        return await self.recorder.send(request, self.native)

    async def aclose(self):
        # Kiwoom opens one AsyncClient per page while retaining its transport.
        # The proof controller owns the final close, not an individual page.
        pass

    async def shutdown(self):
        await self.native.aclose()
