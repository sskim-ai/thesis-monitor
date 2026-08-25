from __future__ import annotations

import math
import statistics
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


MARKET_CROSS_SECTION_VERSION = "market-cross-section-v1"
MARKET_BREADTH_CALCULATION_VERSION = "market-breadth-v1"


class NormalizedMarketRow(BaseModel):
    ticker: str
    session_date: date
    close: float
    previous_close: float | None = None
    volume: float | None = None
    vwap: float | None = None
    security_type: str | None = None
    primary_exchange: str | None = None
    currency: str | None = None
    eligible: bool = False
    exclusion_reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_row(self) -> "NormalizedMarketRow":
        if not self.ticker.strip():
            raise ValueError("ticker is required")
        for value in (self.close, self.previous_close, self.volume, self.vwap):
            if value is not None and not math.isfinite(value):
                raise ValueError("market row values must be finite")
        if self.close <= 0:
            raise ValueError("close must be positive")
        if self.previous_close is not None and self.previous_close <= 0:
            raise ValueError("previous close must be positive")
        if self.volume is not None and self.volume < 0:
            raise ValueError("volume cannot be negative")
        if self.eligible and self.exclusion_reasons:
            raise ValueError("eligible row cannot have exclusion reasons")
        return self

    @property
    def return_pct(self) -> float | None:
        if self.previous_close is None:
            return None
        return (self.close / self.previous_close - 1.0) * 100.0


class MarketIndexFact(BaseModel):
    symbol: str
    label: str
    close: float
    return_pct: float | None = None
    volume: float | None = None
    trading_value: float | None = None
    source_ref: str | None = None


class MarketSectorFact(BaseModel):
    sector: str
    taxonomy: str
    metric_role: Literal["actual_sector_breadth", "sector_price_proxy"]
    return_pct: float | None = None
    advance_ratio: float | None = None
    relative_return_pct: float | None = None
    sector_code: str | None = None
    market_scope: str | None = None
    listed_count: int | None = None
    advance_count: int | None = None
    decline_count: int | None = None
    unchanged_count: int | None = None
    limit_up_count: int | None = None
    limit_down_count: int | None = None
    source_ref: str | None = None


class MarketFlowFact(BaseModel):
    actor: Literal["foreign", "institution", "retail"]
    net_buy_amount: float
    currency: str
    market: str
    exchange_basis: str | None = None
    source_unit: str | None = None
    source_unit_scale_krw: int | None = None
    source_ref: str | None = None


class MarketBreadth(BaseModel):
    eligible_count: int
    advance_count: int
    decline_count: int
    unchanged_count: int
    advance_ratio: float | None
    ad_ratio: float | None
    median_return_pct: float | None
    equal_weight_return_pct: float | None
    positive_return_pct: float | None
    negative_return_pct: float | None
    total_trading_volume: float | None
    total_trading_value: float | None
    listed_count: int | None = None
    limit_up_count: int | None = None
    limit_down_count: int | None = None

    @model_validator(mode="after")
    def validate_counts(self) -> "MarketBreadth":
        if self.eligible_count != (
            self.advance_count + self.decline_count + self.unchanged_count
        ):
            raise ValueError("breadth counts do not reconcile")
        return self


class MarketScopedBreadth(BaseModel):
    scope: str
    breadth: MarketBreadth

    @model_validator(mode="after")
    def validate_scope(self) -> "MarketScopedBreadth":
        if not self.scope.strip():
            raise ValueError("market breadth scope is required")
        return self


class MarketCrossSectionQuality(BaseModel):
    provider: str
    provider_role: str
    coverage: Literal["full", "partial", "unavailable"]
    freshness: Literal["fresh", "stale", "unknown"]
    universe_version: str
    calculation_version: str = MARKET_BREADTH_CALCULATION_VERSION
    raw_count: int = 0
    eligible_count: int = 0
    excluded_count: int = 0
    exclusion_reason_counts: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    volume_semantics: Literal[
        "raw_reported_shares",
        "split_adjusted_aggregate_volume",
        "unknown",
    ] = "unknown"
    trading_value_semantics: Literal[
        "official_reported",
        "deterministic_close_times_raw_volume_estimate",
        "deterministic_close_times_adjusted_volume_estimate",
        "unknown",
    ] = "unknown"


class MarketCrossSection(BaseModel):
    contract_version: Literal["market-cross-section-v1"] = MARKET_CROSS_SECTION_VERSION
    market: Literal["KR", "US"]
    session_date: date
    as_of: datetime
    indices: list[MarketIndexFact] = Field(default_factory=list)
    breadth: MarketBreadth | None = None
    breadth_by_scope: list[MarketScopedBreadth] = Field(default_factory=list)
    concentration: dict[str, object] = Field(default_factory=dict)
    sectors: list[MarketSectorFact] = Field(default_factory=list)
    market_flows: list[MarketFlowFact] = Field(default_factory=list)
    quality: MarketCrossSectionQuality
    source_payload_sha256: str

    @model_validator(mode="after")
    def validate_section(self) -> "MarketCrossSection":
        if self.as_of.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")
        if self.breadth is not None:
            if self.quality.coverage == "unavailable":
                raise ValueError("unavailable coverage cannot publish breadth")
            if self.breadth.eligible_count != self.quality.eligible_count:
                raise ValueError("quality and breadth eligible counts differ")
        scopes = [item.scope for item in self.breadth_by_scope]
        if len(scopes) != len(set(scopes)):
            raise ValueError("market breadth scopes must be unique")
        if self.market == "US" and any(scope != "US_BROAD" for scope in scopes):
            raise ValueError("US cross-section cannot publish KR market breadth scopes")
        if self.market == "KR" and any(
            scope not in {"KOSPI", "KOSDAQ"} for scope in scopes
        ):
            raise ValueError("KR cross-section breadth scope is invalid")
        return self


def calculate_market_breadth(rows: list[NormalizedMarketRow]) -> MarketBreadth:
    eligible = [row for row in rows if row.eligible and row.return_pct is not None]
    returns = [row.return_pct for row in eligible if row.return_pct is not None]
    advance = sum(value > 0 for value in returns)
    decline = sum(value < 0 for value in returns)
    unchanged = len(returns) - advance - decline
    volume_rows = [row.volume for row in eligible if row.volume is not None]
    trading_values = [
        row.close * row.volume
        for row in eligible
        if row.volume is not None and row.close > 0
    ]
    return MarketBreadth(
        eligible_count=len(eligible),
        advance_count=advance,
        decline_count=decline,
        unchanged_count=unchanged,
        advance_ratio=(advance / len(eligible) if eligible else None),
        ad_ratio=(advance / decline if decline else None),
        median_return_pct=(statistics.median(returns) if returns else None),
        equal_weight_return_pct=(statistics.fmean(returns) if returns else None),
        positive_return_pct=(advance / len(eligible) * 100 if eligible else None),
        negative_return_pct=(decline / len(eligible) * 100 if eligible else None),
        total_trading_volume=(sum(volume_rows) if volume_rows else None),
        total_trading_value=(sum(trading_values) if trading_values else None),
    )


def concentration_from_proxy(
    *, proxy_symbol: str, proxy_return_pct: float, equal_weight_return_pct: float
) -> dict[str, object]:
    return {
        "metric_role": "broad_cap_weight_proxy_gap",
        "proxy_symbol": proxy_symbol,
        "proxy_return_pct": proxy_return_pct,
        "equal_weight_return_pct": equal_weight_return_pct,
        "concentration_gap_pct": proxy_return_pct - equal_weight_return_pct,
        "limitations": [
            "The proxy is not a market-cap-weighted whole-market universe.",
        ],
    }


class CrossProviderReconciliation(BaseModel):
    session_date: date
    primary_provider: str
    secondary_provider: str
    comparable: bool
    differences: dict[str, float | int | None] = Field(default_factory=dict)
    reason_codes: list[str] = Field(default_factory=list)


def reconcile_cross_sections(
    primary: MarketCrossSection, secondary: MarketCrossSection
) -> CrossProviderReconciliation:
    reasons: list[str] = []
    comparable = True
    if primary.market != secondary.market or primary.session_date != secondary.session_date:
        comparable = False
        reasons.append("market_or_session_mismatch")
    if primary.quality.universe_version != secondary.quality.universe_version:
        comparable = False
        reasons.append("universe_version_mismatch")
    differences: dict[str, float | int | None] = {}
    if primary.breadth is not None and secondary.breadth is not None:
        for field in ("eligible_count", "advance_count", "decline_count", "unchanged_count"):
            differences[field] = getattr(secondary.breadth, field) - getattr(
                primary.breadth, field
            )
        for field in ("advance_ratio", "equal_weight_return_pct"):
            left = getattr(primary.breadth, field)
            right = getattr(secondary.breadth, field)
            differences[field] = None if left is None or right is None else right - left
    else:
        comparable = False
        reasons.append("breadth_missing")
    return CrossProviderReconciliation(
        session_date=primary.session_date,
        primary_provider=primary.quality.provider,
        secondary_provider=secondary.quality.provider,
        comparable=comparable,
        differences=differences,
        reason_codes=reasons,
    )
