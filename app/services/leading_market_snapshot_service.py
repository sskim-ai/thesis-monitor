from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from app.services.cross_market_decision_engine_service import FrozenModel


CONTRACT_VERSION = "leading-market-snapshot-v1"
CONTEXT_KEY = "leading_market_context"
LeadingMarketReferenceBasis = Literal[
    "PRIOR_OFFICIAL_SETTLEMENT",
    "PROVIDER_DOCUMENTED_REFERENCE",
    "PRIOR_COMPARABLE_NIGHT_CLOSE",
]


class LeadingMarketSessionState(StrEnum):
    ACTIVE_FUTURES_SESSION = "ACTIVE_FUTURES_SESSION"
    PREOPEN_FUTURES_SESSION = "PREOPEN_FUTURES_SESSION"
    STALE_FUTURES_SESSION = "STALE_FUTURES_SESSION"
    CLOSED_NO_CURRENT_FUTURES = "CLOSED_NO_CURRENT_FUTURES"


class LeadingMarketFreshness(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"


class LeadingMarketSourceContract(FrozenModel):
    contract_id: str
    provider: str
    market: Literal["us", "kr"]
    instrument_ids: tuple[str, ...] = Field(min_length=1)
    reference_basis: LeadingMarketReferenceBasis | None = None
    active_max_age_seconds: int = Field(gt=0)
    preopen_max_age_seconds: int = Field(gt=0)
    source_timezone: str
    official_or_existing_supported_free: bool

    @model_validator(mode="after")
    def validate_source(self) -> LeadingMarketSourceContract:
        if len(set(self.instrument_ids)) != len(self.instrument_ids):
            raise ValueError("leading_market_duplicate_source_instrument")
        try:
            ZoneInfo(self.source_timezone)
        except (KeyError, ValueError) as exc:
            raise ValueError("leading_market_source_timezone_invalid") from exc
        return self


class LeadingMarketObservation(FrozenModel):
    instrument_id: str
    display_name: str
    provider: str
    session_id: str
    current_price: float
    reference_price: float | None = None
    change_pct: float | None = None
    reference_basis: LeadingMarketReferenceBasis | None = None
    as_of: datetime
    source_timezone: str
    source_document_or_endpoint: str

    @model_validator(mode="after")
    def validate_observation(self) -> LeadingMarketObservation:
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("leading_market_naive_asof")
        comparison = (self.reference_price, self.change_pct, self.reference_basis)
        if any(value is None for value in comparison) and not all(
            value is None for value in comparison
        ):
            raise ValueError("leading_market_partial_comparison_forbidden")
        numeric_values = [self.current_price]
        if self.reference_price is not None and self.change_pct is not None:
            numeric_values.extend((self.reference_price, self.change_pct))
        if not all(math.isfinite(value) for value in numeric_values):
            raise ValueError("leading_market_nonfinite_value")
        if self.current_price <= 0 or (
            self.reference_price is not None and self.reference_price <= 0
        ):
            raise ValueError("leading_market_nonpositive_price")
        if not all(
            value.strip()
            for value in (
                self.instrument_id,
                self.display_name,
                self.provider,
                self.session_id,
                self.source_document_or_endpoint,
            )
        ):
            raise ValueError("leading_market_observation_identity_missing")
        try:
            ZoneInfo(self.source_timezone)
        except (KeyError, ValueError) as exc:
            raise ValueError("leading_market_observation_timezone_invalid") from exc
        if self.reference_price is not None and self.change_pct is not None:
            expected = (self.current_price / self.reference_price - 1) * 100
            if not math.isclose(expected, self.change_pct, rel_tol=0, abs_tol=0.005):
                raise ValueError("leading_market_change_basis_mismatch")
        return self


class LeadingMarketSnapshot(FrozenModel):
    contract: Literal["leading-market-snapshot-v1"] = CONTRACT_VERSION
    market: Literal["us", "kr"]
    session_state: LeadingMarketSessionState
    observations: tuple[LeadingMarketObservation, ...] = ()
    collected_at: datetime

    @model_validator(mode="after")
    def validate_snapshot(self) -> LeadingMarketSnapshot:
        if self.collected_at.tzinfo is None or self.collected_at.utcoffset() is None:
            raise ValueError("leading_market_naive_collection_time")
        active = self.session_state in {
            LeadingMarketSessionState.ACTIVE_FUTURES_SESSION,
            LeadingMarketSessionState.PREOPEN_FUTURES_SESSION,
        }
        if active != bool(self.observations):
            raise ValueError("leading_market_session_observation_mismatch")
        instruments = [row.instrument_id for row in self.observations]
        if len(instruments) != len(set(instruments)):
            raise ValueError("leading_market_duplicate_observation")
        if len({row.session_id for row in self.observations}) > 1:
            raise ValueError("leading_market_mixed_session")
        return self


class LeadingMarketRenderContext(FrozenModel):
    source_contract: LeadingMarketSourceContract
    snapshot: LeadingMarketSnapshot
    validation_as_of: datetime

    @model_validator(mode="after")
    def validate_context(self) -> LeadingMarketRenderContext:
        if self.validation_as_of.tzinfo is None or self.validation_as_of.utcoffset() is None:
            raise ValueError("leading_market_naive_validation_time")
        return self


class LeadingMarketValidation(FrozenModel):
    valid: bool
    freshness: LeadingMarketFreshness | None
    errors: tuple[str, ...]


class RenderedLeadingMarketBlock(FrozenModel):
    status: Literal["VISIBLE", "OMITTED_STALE", "OMITTED_CLOSED", "INVALID"]
    text: str
    fact_count: int
    validation: LeadingMarketValidation


def validate_leading_market_snapshot(
    snapshot: LeadingMarketSnapshot,
    source: LeadingMarketSourceContract,
    *,
    now: datetime,
) -> LeadingMarketValidation:
    errors: list[str] = []
    if now.tzinfo is None or now.utcoffset() is None:
        errors.append("leading_market_naive_validation_time")
        return LeadingMarketValidation(valid=False, freshness=None, errors=tuple(errors))
    if not source.official_or_existing_supported_free:
        errors.append("leading_market_source_not_eligible")
    if snapshot.market != source.market:
        errors.append("leading_market_source_market_mismatch")
    if snapshot.collected_at.astimezone(UTC) > now.astimezone(UTC):
        errors.append("leading_market_future_collection_time")
    allowed = set(source.instrument_ids)
    for row in snapshot.observations:
        if row.provider != source.provider:
            errors.append(f"leading_market_provider_mismatch:{row.instrument_id}")
        if row.instrument_id not in allowed:
            errors.append(f"leading_market_instrument_not_allowed:{row.instrument_id}")
        if row.reference_basis != source.reference_basis:
            errors.append(f"leading_market_reference_basis_mismatch:{row.instrument_id}")
        if row.source_timezone != source.source_timezone:
            errors.append(f"leading_market_source_timezone_mismatch:{row.instrument_id}")
        if row.as_of.astimezone(UTC) > now.astimezone(UTC):
            errors.append(f"leading_market_future_observation:{row.instrument_id}")
        if row.as_of.astimezone(UTC) > snapshot.collected_at.astimezone(UTC):
            errors.append(f"leading_market_observation_after_collection:{row.instrument_id}")
    freshness: LeadingMarketFreshness | None = None
    if snapshot.observations and not errors:
        max_age = (
            source.active_max_age_seconds
            if snapshot.session_state == LeadingMarketSessionState.ACTIVE_FUTURES_SESSION
            else source.preopen_max_age_seconds
        )
        ages = [
            (now.astimezone(UTC) - row.as_of.astimezone(UTC)).total_seconds()
            for row in snapshot.observations
        ]
        freshness = (
            LeadingMarketFreshness.CURRENT
            if all(age <= max_age for age in ages)
            else LeadingMarketFreshness.STALE
        )
        if freshness == LeadingMarketFreshness.STALE:
            errors.append("leading_market_snapshot_stale")
    return LeadingMarketValidation(
        valid=not errors,
        freshness=freshness,
        errors=tuple(dict.fromkeys(errors)),
    )


def render_leading_market_block(
    snapshot: LeadingMarketSnapshot,
    source: LeadingMarketSourceContract,
    *,
    now: datetime,
) -> RenderedLeadingMarketBlock:
    validation = validate_leading_market_snapshot(snapshot, source, now=now)
    if snapshot.session_state == LeadingMarketSessionState.CLOSED_NO_CURRENT_FUTURES:
        return RenderedLeadingMarketBlock(
            status="OMITTED_CLOSED",
            text="",
            fact_count=0,
            validation=validation,
        )
    if snapshot.session_state == LeadingMarketSessionState.STALE_FUTURES_SESSION:
        return RenderedLeadingMarketBlock(
            status="OMITTED_STALE",
            text="",
            fact_count=0,
            validation=validation,
        )
    if not validation.valid:
        status = (
            "OMITTED_STALE"
            if "leading_market_snapshot_stale" in validation.errors
            else "INVALID"
        )
        return RenderedLeadingMarketBlock(
            status=status,
            text="",
            fact_count=0,
            validation=validation,
        )
    latest = max(row.as_of for row in snapshot.observations)
    kst = latest.astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M KST")
    heading = "현재 선행시장" if snapshot.market == "us" else "현재 선행시장 / 야간선물"
    lines = [f"⏱ {heading} · {kst}"]
    lines.extend(
        (
            f"• {row.display_name} {row.change_pct:+.2f}%"
            if row.change_pct is not None
            else f"• {row.display_name} {row.current_price:,.2f}"
        )
        for row in snapshot.observations
    )
    lines.append("• 선물은 현재 선행 신호이며 완료된 정규장 신호가 아닙니다.")
    return RenderedLeadingMarketBlock(
        status="VISIBLE",
        text="\n".join(lines),
        fact_count=len(snapshot.observations),
        validation=validation,
    )


def leading_market_block_from_context(
    context: Mapping[str, object],
    *,
    expected_market: Literal["us", "kr"],
) -> RenderedLeadingMarketBlock | None:
    raw = context.get(CONTEXT_KEY)
    if raw is None:
        return None
    parsed = LeadingMarketRenderContext.model_validate(raw)
    if parsed.snapshot.market != expected_market:
        raise ValueError("leading_market_render_market_mismatch")
    return render_leading_market_block(
        parsed.snapshot,
        parsed.source_contract,
        now=parsed.validation_as_of,
    )
