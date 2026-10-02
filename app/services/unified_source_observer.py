"""Opt-in, bounded OHLCV wire evidence. Receipt success is not source qualification.

The request plan is frozen before dispatch. Raw bodies and normalization receipts
are separate immutable artifacts, including failed requests and malformed refetches.
No headers, credentials, exception text, or arbitrary endpoint URL is exported.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Literal
from collections.abc import Awaitable, Callable

import httpx
from pydantic import Field, model_validator, model_serializer

from app.services.unified_run_artifacts import durable_bytes, durable_json, SECRET_KEY, SECRET_VALUE
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_source_policy import UnifiedSourcePolicy


def _secret_field(value: object) -> bool:
    if isinstance(value, dict):
        return any(SECRET_KEY.search(str(k)) or _secret_field(v) for k, v in value.items())
    return isinstance(value, list) and any(_secret_field(v) for v in value)


async def capture_source_response(*, root: Path, identity: str, receipt: dict,
                                  send: Callable[[], Awaitable[httpx.Response]]) -> httpx.Response:
    """Shared data-only wire capture. Callers never pass auth headers or auth bodies."""
    durable_json(root / f"{identity}.intent.json", receipt, exclusive=True)
    try:
        response = await send()
    except httpx.HTTPError as exc:
        durable_json(root / f"{identity}.response.json", {
            **receipt, "received_at": datetime.now(timezone.utc).isoformat(),
            "outcome": "TRANSPORT_ERROR", "error_class": type(exc).__name__,
            "artifact": None, "artifact_sha256": None,
        }, exclusive=True)
        raise
    raw = response.content
    response_receipt = {
        **receipt, "received_at": datetime.now(timezone.utc).isoformat(),
        "http_status": response.status_code, "artifact": f"{identity}.body",
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "outcome": "HTTP_RESPONSE", "raw_representation": "httpx_response_content",
    }
    try:
        secret_field = _secret_field(response.json())
    except ValueError:
        secret_field = False
    if SECRET_VALUE.search(raw.decode("utf-8", errors="replace")) or secret_field:
        durable_json(root / f"{identity}.response.json", {
            **response_receipt, "artifact": None, "artifact_sha256": None,
            "outcome": "BODY_WITHHELD_SECRET_RISK",
        }, exclusive=True)
        raise ValueError("source_response_secret_risk")
    durable_bytes(root / response_receipt["artifact"], raw, exclusive=True)
    durable_json(root / f"{identity}.response.json", response_receipt, exclusive=True)
    response.extensions["unified_source_receipt"] = (identity, response_receipt)
    return response


class OhlcvRead(ContractModel):
    role: str = Field(min_length=1)
    symbol: str = Field(pattern=r"^[A-Za-z0-9.^_-]+$")
    market: Literal["us", "kr"]
    provider: str = Field(min_length=1)
    response_provider: Literal["kiwoom"] | None = None
    period: Literal["daily", "weekly", "monthly"]
    adjusted: bool
    session_date: date
    params: dict[str, str | int]
    max_requests: int = Field(ge=1, le=10)

    @model_serializer(mode="wrap")
    def preserve_legacy_wire_shape(self, handler):
        value = handler(self)
        if self.response_provider is None:
            value.pop("response_provider", None)
        return value

    @model_validator(mode="after")
    def request_identity(self):
        allowed = {"symbol", "market", "periods", "count", "include_indicators",
                   "indicator_limit", "adjusted"}
        if set(self.params) - allowed:
            raise ValueError("source_request_field_not_authorized")
        if (self.params.get("symbol"), self.params.get("periods"),
            self.params.get("adjusted")) != (self.symbol, self.period, str(self.adjusted).lower()):
            raise ValueError("source_request_identity_mismatch")
        if str(self.params.get("market", self.market)).lower() != self.market:
            raise ValueError("source_request_market_mismatch")
        return self


class OhlcvReceiptObserver:
    def __init__(self, *, root: Path, run_id: str, attempt_id: str,
                 reads: tuple[OhlcvRead, ...], policy: UnifiedSourcePolicy) -> None:
        if not run_id or not attempt_id or not reads or root.exists():
            raise ValueError("new_source_attempt_root_and_identity_required")
        if any(parent.is_symlink() for parent in (root, *root.parents)):
            raise ValueError("source_artifact_symlink")
        identities = [digest(r.params) for r in reads]
        if len(set(identities)) != len(reads) or len({r.role for r in reads}) != len(reads):
            raise ValueError("duplicate_source_read_identity")
        for read in reads:
            policy.require(read.provider)
            if read.response_provider is not None:
                policy.require(read.response_provider)
        self.root, self.run_id, self.attempt_id = root, run_id, attempt_id
        self.policy = policy
        # Pydantic frozen models do not recursively freeze dictionaries.
        self._plan = json.dumps([r.model_dump(mode="json") for r in reads], sort_keys=True)
        self._counts: dict[str, int] = {}
        self._ordinal = 0
        self._pending: set[str] = set()
        durable_json(root / "plan.json", {"run_id": run_id, "attempt_id": attempt_id,
                     "acquisition_class": "ATTEMPT_FRESH", "reads": json.loads(self._plan)},
                     exclusive=True)

    @property
    def reads(self) -> tuple[OhlcvRead, ...]:
        return tuple(OhlcvRead.model_validate(r) for r in json.loads(self._plan))

    def require_market_set(self, symbols: set[str]) -> None:
        if self._ordinal or len(self.reads) != len(symbols) or {
            r.symbol for r in self.reads
        } != symbols or len({r.session_date for r in self.reads}) != 1:
            raise ValueError("whole_fresh_market_plan_required")
        if any(r.market != "us" or r.period != "daily" or not r.adjusted
               or r.provider != "ohlcv_analyst"
               for r in self.reads):
            raise ValueError("market_plan_basis_mismatch")

    async def get(self, client: httpx.AsyncClient, route: str, *, params: dict) -> httpx.Response:
        reads = tuple(OhlcvRead.model_validate(r) for r in json.loads(self._plan))
        selected = [r for r in reads if r.params == params]
        if route != "/ohlcv" or len(selected) != 1:
            raise ValueError("source_request_outside_frozen_plan")
        read = selected[0]
        count = self._counts.get(read.role, 0) + 1
        if count > read.max_requests:
            raise ValueError("source_request_budget_exhausted")
        self._counts[read.role] = count
        self._ordinal += 1
        identity = f"read-{self._ordinal:04d}"
        request = {"method": "GET", "route": route, "params": params}
        receipt = {"run_id": self.run_id, "attempt_id": self.attempt_id,
                   "acquisition_class": "ATTEMPT_FRESH", "ordinal": self._ordinal,
                   "role_ordinal": count, "read": read.model_dump(mode="json"),
                   "role": read.role, "market": read.market, "symbol": read.symbol,
                   "provider": read.provider, "session": read.session_date.isoformat(),
                   "basis": "adjusted_close" if read.adjusted else "unadjusted_close",
                   "request": request, "request_sha256": digest(request),
                   "requested_at": datetime.now(timezone.utc).isoformat()}
        response = await capture_source_response(root=self.root, identity=identity,
            receipt=receipt, send=lambda: client.get(route, params=params))
        self._pending.add(identity)
        return response

    def normalized(self, response: httpx.Response, *, normalized: dict,
                   contract: str, valid: bool, fingerprint: str) -> None:
        identity, receipt = response.extensions["unified_source_receipt"]
        if identity not in self._pending:
            raise ValueError("source_receipt_already_normalized")
        payload = response.json()
        self.policy.check_lineage(payload)
        meta, resolved = payload.get("meta", {}), payload.get("resolved_symbol", {})
        if not isinstance(meta, dict) or not isinstance(resolved, dict):
            raise ValueError("source_response_identity_missing_or_mismatched")
        read = receipt["read"]
        if (resolved.get("code"), meta.get("provider")) != (
                read["symbol"], read.get("response_provider") or read["provider"]):
            raise ValueError("source_response_identity_missing_or_mismatched")
        if type(meta.get("adjusted")) is not bool or meta["adjusted"] != read["adjusted"]:
            raise ValueError("source_response_basis_mismatch")
        durable_json(self.root / f"{identity}.normalization.json", {
            "run_id": self.run_id, "attempt_id": self.attempt_id,
            "role": receipt["read"]["role"], "raw_sha256": receipt["artifact_sha256"],
            "response_receipt_sha256": digest(receipt),
            "normalized": normalized, "normalized_sha256": digest(normalized),
            "validator_contract": contract, "valid": valid,
            "validator_fingerprint": fingerprint,
            "qualification": "NORMALIZATION_ONLY_SESSION_AUTHORITY_NOT_QUALIFIED",
        }, exclusive=True)
        self._pending.remove(identity)
