from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows


CONTRACT_VERSION = "ohlcv-secondary-exact-row-recovery-v1"


class SecondaryRecoveryStatus(StrEnum):
    RECOVERED = "RECOVERED_FULL_OR_PARTIAL"
    NO_APPROVED_SOURCE = "NO_APPROVED_SECONDARY_SOURCE"
    NOT_COMPARABLE = "SECONDARY_NOT_COMPARABLE"
    SECONDARY_INVALID = "SECONDARY_ALSO_INVALID"


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SecondarySourcePolicy(FrozenModel):
    provider: str
    approved_for_production_ohlcv: bool
    security_identity_exact: bool
    session_exact: bool
    currency_exact: bool
    adjustment_basis_compatible: bool
    timestamp_safe: bool
    scale_compatible: bool


class SecondaryRecoveryResult(FrozenModel):
    contract: str = CONTRACT_VERSION
    status: SecondaryRecoveryStatus
    recovered_row: dict[str, object] | None = None
    primary_bad_fingerprint: str
    secondary_fingerprint: str | None = None
    provider: str | None = None
    denial_reasons: tuple[str, ...] = ()


def _sha(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def recover_exact_bad_row(
    *,
    primary_bad_row: Mapping[str, object],
    secondary_row: Mapping[str, object] | None,
    timeframe: str,
    policy: SecondarySourcePolicy | None,
) -> SecondaryRecoveryResult:
    primary_sha = _sha(primary_bad_row)
    if secondary_row is None or policy is None or not policy.approved_for_production_ohlcv:
        return SecondaryRecoveryResult(
            status=SecondaryRecoveryStatus.NO_APPROVED_SOURCE,
            primary_bad_fingerprint=primary_sha,
            provider=policy.provider if policy is not None else None,
            denial_reasons=("provider_not_approved_for_production_ohlcv",),
        )
    checks = {
        "security_identity_mismatch": policy.security_identity_exact,
        "session_mismatch": policy.session_exact,
        "currency_mismatch": policy.currency_exact,
        "adjustment_basis_mismatch": policy.adjustment_basis_compatible,
        "timestamp_unsafe": policy.timestamp_safe,
        "scale_mismatch": policy.scale_compatible,
        "date_mismatch": str(primary_bad_row.get("date")) == str(secondary_row.get("date")),
    }
    denial = tuple(reason for reason, passed in checks.items() if not passed)
    secondary_sha = _sha(secondary_row)
    if denial:
        return SecondaryRecoveryResult(
            status=SecondaryRecoveryStatus.NOT_COMPARABLE,
            primary_bad_fingerprint=primary_sha,
            secondary_fingerprint=secondary_sha,
            provider=policy.provider,
            denial_reasons=denial,
        )
    inspection = inspect_normalized_ohlcv_rows([secondary_row], timeframe=timeframe)
    if not inspection.valid:
        return SecondaryRecoveryResult(
            status=SecondaryRecoveryStatus.SECONDARY_INVALID,
            primary_bad_fingerprint=primary_sha,
            secondary_fingerprint=secondary_sha,
            provider=policy.provider,
            denial_reasons=tuple(sorted({issue.violation for issue in inspection.issues})),
        )
    recovered = dict(secondary_row)
    recovered["_recovery_provenance"] = {
        "contract": CONTRACT_VERSION,
        "provider": policy.provider,
        "primary_bad_fingerprint": primary_sha,
        "secondary_fingerprint": secondary_sha,
        "whole_series_swap": False,
        "cross_provider_averaging": False,
    }
    return SecondaryRecoveryResult(
        status=SecondaryRecoveryStatus.RECOVERED,
        recovered_row=recovered,
        primary_bad_fingerprint=primary_sha,
        secondary_fingerprint=secondary_sha,
        provider=policy.provider,
    )


def approved_runtime_secondary_sources() -> tuple[str, ...]:
    # Massive is shadow market-internals only and Alpha Vantage has no implemented
    # historical OHLCV adapter in this repository. Neither is runtime-approved here.
    return ()
