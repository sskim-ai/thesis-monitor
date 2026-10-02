"""Offline OHLCV role replay using the existing parser and integrity owner.

This is a source-adapter component, not production adapter qualification.
The manifest and role specification must be frozen independently of replay.
No filesystem search, cache substitution, network, or model invocation occurs.
"""

from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field

from app.services.ohlcv_client import OhlcvClient
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.unified_snapshot_contract import ContractModel, SourceReceipt, digest
from app.services.unified_source_policy import prohibited_provider


class FrozenOhlcvRole(ContractModel):
    run_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    market: Literal["us", "kr"]
    role: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    period: Literal["daily", "weekly", "monthly"]
    adjusted: bool
    latest_row_date: date
    requested_at: datetime
    received_at: datetime
    request: dict
    request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifact: str = Field(min_length=1)
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    normalized_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class ReplayedOhlcvRole(ContractModel):
    receipt: SourceReceipt
    normalized: dict
    request_sha256: str
    validator_contract: str
    validator_fingerprint: str
    qualification: Literal["ROLE_ONLY_NOT_PRODUCTION_ADAPTER"] = "ROLE_ONLY_NOT_PRODUCTION_ADAPTER"


def read_bound_artifact(root: Path, relative: str, expected_sha256: str) -> bytes:
    """Accept one named, regular artifact below the sealed attempt root only."""
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(p in {".", ".."} for p in path.parts):
        raise ValueError("source_artifact_path_invalid")
    current = root
    if any(parent.is_symlink() for parent in (root, *root.parents)):
        raise ValueError("source_artifact_symlink")
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("source_artifact_symlink")
    if not current.resolve().is_relative_to(root.resolve()) or not current.is_file():
        raise ValueError("source_artifact_missing")
    data = current.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("source_artifact_hash_mismatch")
    return data


def replay_ohlcv_role(
    spec: FrozenOhlcvRole, *, root: Path, run_id: str, attempt_id: str,
    market: str, started_at: datetime, completed_at: datetime,
) -> ReplayedOhlcvRole:
    if (spec.run_id, spec.attempt_id, spec.market) != (run_id, attempt_id, market):
        raise ValueError("source_attempt_identity_mismatch")
    times = (started_at, spec.requested_at, spec.received_at, completed_at)
    if any(t.utcoffset() is None for t in times):
        raise ValueError("source_timezone_required")
    if not started_at <= spec.requested_at <= spec.received_at <= completed_at:
        raise ValueError("source_request_outside_attempt")
    if spec.latest_row_date > completed_at.astimezone(spec.received_at.tzinfo).date():
        raise ValueError("source_row_after_collection")
    if prohibited_provider(spec.provider):
        raise ValueError("source_provider_not_authorized")
    if digest(spec.request) != spec.request_sha256:
        raise ValueError("source_request_hash_mismatch")
    params = spec.request.get("params", {})
    if (spec.request.get("method"), spec.request.get("route"), params.get("symbol"),
        params.get("periods"), params.get("adjusted")) != (
            "GET", "/ohlcv", spec.symbol, spec.period, str(spec.adjusted).lower()):
        raise ValueError("source_request_role_mismatch")
    if params.get("market", market).lower() != market:
        raise ValueError("source_request_market_mismatch")
    payload = json.loads(read_bound_artifact(root, spec.artifact, spec.artifact_sha256))
    if not isinstance(payload, dict):
        raise ValueError("source_payload_invalid")
    meta = payload.get("meta", {})
    resolved = payload.get("resolved_symbol", {})
    if not isinstance(meta, dict) or not isinstance(resolved, dict):
        raise ValueError("source_payload_identity_missing")
    # The existing decoder permits absent identity metadata; replay qualification does not.
    if (resolved.get("code"), meta.get("provider")) != (spec.symbol, spec.provider):
        raise ValueError("source_payload_identity_mismatch")
    if type(meta.get("adjusted")) is not bool or meta["adjusted"] != spec.adjusted:
        raise ValueError("source_payload_basis_mismatch")
    if prohibited_provider(str(meta.get("upstream_provider", spec.provider))):
        raise ValueError("source_upstream_not_authorized")
    bars, supply, _provider = OhlcvClient._decode_period_payload(
        payload, ticker=spec.symbol, period=spec.period, adjusted=spec.adjusted,
    )
    inspection = inspect_normalized_ohlcv_rows(
        bars, timeframe=spec.period, cutoff=spec.latest_row_date,
    )
    if not bars or not inspection.valid:
        raise ValueError("source_ohlcv_integrity_failed")
    if str(bars[-1].get("date", ""))[:10] != spec.latest_row_date.isoformat():
        raise ValueError("source_latest_row_mismatch")
    normalized = {"bars": bars, "supply_demand": supply}
    if digest(normalized) != spec.normalized_sha256:
        raise ValueError("source_normalization_binding_mismatch")
    return ReplayedOhlcvRole(
        receipt=SourceReceipt(
            role=spec.role, attempt_id=attempt_id, provider=spec.provider,
            route="/ohlcv", symbol=spec.symbol, session_date=spec.latest_row_date,
            basis="adjusted_close" if spec.adjusted else "unadjusted_close",
            observed_at=spec.received_at, raw_sha256=spec.artifact_sha256,
            normalized_sha256=spec.normalized_sha256, status="PASS",
        ),
        normalized=normalized, request_sha256=spec.request_sha256,
        validator_contract=inspection.contract,
        validator_fingerprint=inspection.payload_fingerprint,
    )
