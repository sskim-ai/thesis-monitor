from __future__ import annotations

from decimal import Decimal

from app.services.price_structure_wave_fibonacci_v3_service import (
    LongHistoryCoverage,
    TechnicalZone,
    ZoneSource,
    build_deterministic_sr_base_layer,
    merge_zone_sources,
)


def _source(
    identifier: str,
    price: str,
    *,
    timeframe: str = "daily",
    role: str | None = None,
    status: str = "CONFIRMED",
    evidence_type: str = "PIVOT",
    stability: str | None = None,
) -> ZoneSource:
    return ZoneSource(
        source_id=identifier,
        evidence_type=evidence_type,
        evidence_family=f"{evidence_type}_{timeframe.upper()}",
        method_family="TEST",
        source_timeframe=timeframe,
        source_degree=f"{timeframe.upper()}_PRICE_STRUCTURE",
        confluence_target_timeframe=timeframe,
        price=Decimal(price),
        status=status,
        family_stability=stability,
        interaction_date="2026-08-20",
        source_role=role,
    )


def _zone(
    identifier: str,
    low: str,
    high: str,
    *,
    timeframe: str = "daily",
    role: str = "SUPPORT",
    structural: int = 11,
    quality: str = "1",
    reaction_count: int = 1,
    sources: tuple[ZoneSource, ...] | None = None,
) -> TechnicalZone:
    low_value = Decimal(low)
    high_value = Decimal(high)
    center = (low_value + high_value) / Decimal(2)
    current = Decimal(100)
    distance = (
        (current - high_value) / current * Decimal(100)
        if role == "SUPPORT"
        else (low_value - current) / current * Decimal(100)
        if role == "RESISTANCE"
        else Decimal(0)
    )
    return TechnicalZone(
        zone_id=identifier,
        ticker="TEST",
        timeframe=timeframe,
        low=low_value,
        high=high_value,
        center=center,
        current_role=role,
        structural_importance=structural,
        proximity_pct=distance,
        evidence_family_score=Decimal("1"),
        confirmation_quality=Decimal(quality),
        reaction_count=reaction_count,
        last_meaningful_interaction="2026-08-20",
        sources=sources
        or (
            _source(
                f"source:{identifier}",
                str(center),
                timeframe=timeframe,
                role="SUPPORT" if role == "SUPPORT" else "RESISTANCE",
            ),
        ),
    )


def _coverage(actual: int = 100) -> dict[str, LongHistoryCoverage]:
    return {
        timeframe: LongHistoryCoverage(
            timeframe=timeframe,
            requested_count={"daily": 1200, "weekly": 600, "monthly": 300}[timeframe],
            provider_returned_count=actual,
            actual_count=actual,
            completed_count=actual,
            actual_start_date="2020-01-01",
            actual_end_date="2026-08-20",
            provider_limit=None,
            provider_limit_hit=False,
            history_complete_to_listing=True,
            adjustment_basis="adjusted_close",
            status="PASS" if actual >= 10 else "FAIL",
        )
        for timeframe in ("monthly", "weekly", "daily")
    }


def _build(
    maps: dict[str, tuple[TechnicalZone, ...]],
    *,
    combined: dict[str, tuple[TechnicalZone, ...]] | None = None,
    coverage: dict[str, LongHistoryCoverage] | None = None,
    wave: str = "NONE",
):
    normalized = {timeframe: maps.get(timeframe, ()) for timeframe in ("monthly", "weekly", "daily")}
    return build_deterministic_sr_base_layer(
        ticker="TEST",
        currency="USD",
        as_of="2026-08-26",
        current_price=Decimal(100),
        coverage=coverage or _coverage(),
        deterministic_maps=normalized,
        combined_maps=combined or normalized,
        primary_hypothesis_status=wave,
    )


def test_nearest_uses_quality_floor_then_proximity() -> None:
    noisy = _zone("noisy", "98.9", "99.1", quality="0.4")
    valid = _zone("valid", "94", "96")
    result = _build({"daily": (noisy, valid)})

    assert result.summary.nearest_support.zone is not None
    assert result.summary.nearest_support.zone.zone_id == "valid"


def test_nearest_and_major_are_separate_rankings() -> None:
    nearest = _zone("nearest", "96", "98", structural=11)
    major = _zone("major", "89", "91", structural=19, reaction_count=9)
    result = _build({"daily": (nearest, major)})

    assert result.timeframes["daily"].nearest_support.zone.zone_id == "nearest"  # type: ignore[union-attr]
    assert result.timeframes["daily"].major_support.zone.zone_id == "major"  # type: ignore[union-attr]


def test_current_zone_is_not_reused_as_support_or_resistance() -> None:
    current = _zone("current", "99", "101", role="CURRENT_ZONE")
    support = _zone("support", "94", "96")
    resistance = _zone("resistance", "104", "106", role="RESISTANCE")
    result = _build({"daily": (current, support, resistance)})
    selected = result.timeframes["daily"]

    assert selected.current_zone.zone_id == "current"  # type: ignore[union-attr]
    assert selected.nearest_support.zone.zone_id == "support"  # type: ignore[union-attr]
    assert selected.nearest_resistance.zone.zone_id == "resistance"  # type: ignore[union-attr]


def test_remote_cross_zone_never_displaces_closer_local_sr() -> None:
    local_support = _zone("local-support", "94", "96", timeframe="daily")
    local_resistance = _zone(
        "local-resistance", "104", "106", timeframe="daily", role="RESISTANCE"
    )
    monthly_remote = _zone(
        "monthly-remote",
        "19",
        "21",
        timeframe="monthly",
        structural=39,
        sources=(
            _source("monthly:remote", "20", timeframe="monthly", role="SUPPORT"),
        ),
    )
    weekly_remote = _zone(
        "weekly-remote",
        "19.5",
        "20.5",
        timeframe="weekly",
        structural=29,
        sources=(
            _source("weekly:remote", "20.2", timeframe="weekly", role="SUPPORT"),
        ),
    )
    result = _build(
        {
            "monthly": (monthly_remote,),
            "weekly": (weekly_remote,),
            "daily": (local_support, local_resistance),
        }
    )

    assert result.summary.nearest_support.zone.zone_id == "local-support"  # type: ignore[union-attr]
    assert result.summary.nearest_resistance.zone.zone_id == "local-resistance"  # type: ignore[union-attr]
    assert result.summary.nearest_cross_timeframe_zone is None
    assert result.summary.nearest_cross_timeframe_reason == "NO_RELEVANT_CROSS_TIMEFRAME_ZONE"


def test_daily_missing_side_uses_weekly_fallback_with_provenance() -> None:
    weekly = _zone("weekly-resistance", "108", "110", timeframe="weekly", role="RESISTANCE")
    result = _build({"weekly": (weekly,)})
    selection = result.timeframes["daily"].nearest_resistance

    assert selection.classification == "AVAILABLE_HIGHER_TF_FALLBACK"
    assert selection.zone.source_timeframe == "weekly"  # type: ignore[union-attr]
    assert selection.zone.requested_timeframe == "daily"  # type: ignore[union-attr]
    assert selection.zone.fallback_reason == "NO_LOCAL_RESISTANCE_DAILY"  # type: ignore[union-attr]


def test_short_history_has_explicit_reason_without_fabrication() -> None:
    coverage = _coverage()
    coverage["monthly"] = coverage["monthly"].model_copy(
        update={"actual_count": 2, "completed_count": 2, "status": "FAIL"}
    )
    result = _build({}, coverage=coverage)

    assert result.timeframes["monthly"].nearest_support.classification == "INSUFFICIENT_HISTORY"
    assert result.timeframes["monthly"].nearest_support.zone is None
    assert result.fabricated_fill == 0


def test_no_wave_keeps_sr_and_safe_fib_is_optional_confluence() -> None:
    base_source = _source("base", "95", role="SUPPORT")
    fib_source = _source(
        "fib",
        "95.2",
        evidence_type="FIBONACCI",
        stability="EXACT_INVARIANT",
    )
    base = _zone("base-zone", "94", "96", sources=(base_source,))
    combined = _zone("combined-zone", "94", "96", sources=(base_source, fib_source))
    result = _build(
        {"daily": (base,)},
        combined={"monthly": (), "weekly": (), "daily": (combined,)},
    )

    assert result.summary.no_wave_reason == "NO_VALID_WAVE"
    assert result.summary.nearest_support.zone.zone_id == "base-zone"  # type: ignore[union-attr]
    assert result.summary.fib_sr_confluence is not None
    assert result.summary.fib_sr_confluence_state == "DIRECT_SR_CONFLUENCE"


def test_role_conversion_uses_current_role() -> None:
    source = _source("old-resistance", "90", role="RESISTANCE")
    zone = merge_zone_sources(
        (source,),
        ticker="TEST",
        timeframe="daily",
        current_price=Decimal(100),
    )[0]

    assert zone.historical_role == "RESISTANCE"
    assert zone.current_role == "SUPPORT"
    assert zone.reclaim_status == "RECLAIMED"
