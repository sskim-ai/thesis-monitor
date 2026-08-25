from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.config import get_settings


OFFICIAL_BASE_URL = "https://api.kiwoom.com"
TOKEN_PATH = "/oauth2/token"


class KiwoomRestError(RuntimeError):
    """A secret-safe Kiwoom transport or provider-contract failure."""


def validate_kiwoom_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Kiwoom REST base URL must be an absolute HTTPS URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Kiwoom REST base URL cannot contain credentials or query data")
    return value.rstrip("/")


def payload_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class KiwoomRestResponse:
    api_id: str
    payload: dict[str, Any]
    continuation: bool
    next_key: str
    payload_sha256: str


@dataclass(frozen=True)
class KiwoomCallStats:
    requests: int
    successes: int
    failures: int
    retries: int


class KiwoomRestClient:
    """Minimal official Kiwoom REST client with no account/trading surface."""

    def __init__(
        self,
        *,
        app_key: str | None = None,
        secret_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        request_interval_seconds: float | None = None,
        max_retries: int | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        settings = get_settings()
        self.app_key = app_key if app_key is not None else settings.kiwoom_app_key
        self.secret_key = (
            secret_key if secret_key is not None else settings.kiwoom_secret_key
        )
        self.base_url = validate_kiwoom_base_url(
            base_url or settings.kiwoom_rest_base_url
        )
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.kiwoom_rest_timeout_seconds
        )
        self.request_interval_seconds = (
            request_interval_seconds
            if request_interval_seconds is not None
            else settings.kiwoom_rest_request_interval_seconds
        )
        self.max_retries = (
            max_retries if max_retries is not None else settings.kiwoom_rest_max_retries
        )
        self.transport = transport
        self._token: str | None = None
        self._token_expires_at: datetime | None = None
        self._last_request_at: float | None = None
        self._requests = 0
        self._successes = 0
        self._failures = 0
        self._retries = 0

    @property
    def configured(self) -> bool:
        return bool(self.app_key and self.secret_key)

    @property
    def stats(self) -> KiwoomCallStats:
        return KiwoomCallStats(
            requests=self._requests,
            successes=self._successes,
            failures=self._failures,
            retries=self._retries,
        )

    async def _access_token(self, client: httpx.AsyncClient) -> str:
        if (
            self._token
            and self._token_expires_at
            and datetime.now() < self._token_expires_at - timedelta(minutes=1)
        ):
            return self._token
        if not self.configured:
            raise KiwoomRestError("Kiwoom REST credentials are not configured")
        self._requests += 1
        try:
            response = await client.post(
                TOKEN_PATH,
                json={
                    "grant_type": "client_credentials",
                    "appkey": self.app_key,
                    "secretkey": self.secret_key,
                },
                headers={"Content-Type": "application/json;charset=UTF-8"},
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or int(payload.get("return_code", 0)) != 0:
                raise KiwoomRestError("Kiwoom token request was rejected")
            token = payload.get("token")
            expires_raw = payload.get("expires_dt")
            if not token or not expires_raw:
                raise KiwoomRestError("Kiwoom token response is incomplete")
            expires_at = datetime.strptime(str(expires_raw), "%Y%m%d%H%M%S")
        except (httpx.HTTPError, TypeError, ValueError) as exc:
            self._failures += 1
            raise KiwoomRestError("Kiwoom token request failed") from exc
        self._successes += 1
        self._token = str(token)
        self._token_expires_at = expires_at
        return self._token

    async def _rate_limit(self) -> None:
        if self._last_request_at is not None:
            elapsed = time.monotonic() - self._last_request_at
            delay = max(self.request_interval_seconds - elapsed, 0.0)
            if delay:
                await asyncio.sleep(delay)
        self._last_request_at = time.monotonic()

    async def request(
        self,
        *,
        endpoint: str,
        api_id: str,
        body: dict[str, str],
        continuation: bool = False,
        next_key: str = "",
    ) -> KiwoomRestResponse:
        if not endpoint.startswith("/api/dostk/"):
            raise ValueError("Kiwoom market request endpoint is outside the allowlisted API")
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            transport=self.transport,
        ) as client:
            token = await self._access_token(client)
            for attempt in range(self.max_retries + 1):
                await self._rate_limit()
                self._requests += 1
                try:
                    response = await client.post(
                        endpoint,
                        json=body,
                        headers={
                            "Content-Type": "application/json;charset=UTF-8",
                            "authorization": f"Bearer {token}",
                            "api-id": api_id,
                            "cont-yn": "Y" if continuation else "N",
                            "next-key": next_key,
                        },
                    )
                    if response.status_code == 429 and attempt < self.max_retries:
                        self._retries += 1
                        retry_after = response.headers.get("Retry-After")
                        await asyncio.sleep(float(retry_after) if retry_after else 2**attempt)
                        continue
                    response.raise_for_status()
                    payload = response.json()
                    if not isinstance(payload, dict):
                        raise KiwoomRestError(f"Kiwoom response is not an object: {api_id}")
                    if int(payload.get("return_code", 0)) != 0:
                        raise KiwoomRestError(f"Kiwoom provider rejected request: {api_id}")
                except (httpx.HTTPError, KiwoomRestError, TypeError, ValueError) as exc:
                    self._failures += 1
                    raise KiwoomRestError(f"Kiwoom request failed: {api_id}") from exc
                response_continuation = (
                    str(response.headers.get("cont-yn") or "N").upper() == "Y"
                )
                response_next_key = str(response.headers.get("next-key") or "")
                if response_continuation and not response_next_key:
                    self._failures += 1
                    raise KiwoomRestError(
                        f"Kiwoom continuation response lacks next-key: {api_id}"
                    )
                self._successes += 1
                return KiwoomRestResponse(
                    api_id=api_id,
                    payload=payload,
                    continuation=response_continuation,
                    next_key=response_next_key,
                    payload_sha256=payload_sha256(payload),
                )
        self._failures += 1
        raise KiwoomRestError(f"Kiwoom retry budget exhausted: {api_id}")
