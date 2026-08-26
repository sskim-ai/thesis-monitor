from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.services.multi_timeframe_price_structure_service import (
    PivotEvidence,
    build_price_structure_evidence_packet,
    reference_select_price_structure,
)
from app.services.variable_ai_anchor_selection_service import (
    PACKET_CONTRACT,
    AlternativeAnchorSelection,
    StabilityClass,
    VariableAIAnchorOutput,
    VariableTimeframeSelection,
    audit_price_only_evidence_egress,
    build_price_only_ai_anchor_packet,
    classify_anchor_stability,
    execute_variable_anchor_selector,
    validate_variable_ai_anchor_output,
)


def _swing(timeframe: str, kind: str, date: str, price: float, confirmed_at: str) -> dict:
    return {
        "index": 1,
        "date": date,
        "price": price,
        "kind": kind,
        "timeframe": timeframe,
        "threshold": 1,
        "atr": 1,
        "pct_threshold": 0.1,
        "bars_since_previous": 3,
        "confirmed_at": confirmed_at,
    }


def _zone(timeframe: str, pivot_type: str, low: float, high: float) -> dict:
    return {
        "zone_low": low,
        "zone_high": high,
        "center": (low + high) / 2,
        "pivot_type": pivot_type,
        "pivot_dates": ["2025-01-01"],
        "pivot_prices": [(low + high) / 2],
        "timeframe": timeframe,
        "strength": "Strong",
        "score": 9,
    }


def _structure(*, future_daily: bool = False) -> dict:
    daily_confirmed = "2026-09-01" if future_daily else "2026-08-20"
    return {
        "algorithm_version": "ohlcv-structure-v2",
        "as_of_date": "2026-08-25",
        "price_basis": "adjusted_close",
        "all_zones": [
            _zone("monthly", "low", 90, 100),
            _zone("monthly", "high", 190, 200),
            _zone("weekly", "low", 125, 130),
            _zone("weekly", "high", 170, 175),
            _zone("daily", "low", 145, 147),
            _zone("daily", "high", 155, 157),
        ],
        "major_swings": {
            "by_timeframe": {
                "monthly": [
                    _swing("monthly", "low", "2020-01-01", 50, "2020-03-01"),
                    _swing("monthly", "high", "2023-01-01", 180, "2023-03-01"),
                    _swing("monthly", "low", "2024-01-01", 110, "2024-03-01"),
                ],
                "weekly": [
                    _swing("weekly", "low", "2025-01-06", 100, "2025-01-27"),
                    _swing("weekly", "high", "2025-10-06", 165, "2025-10-27"),
                    _swing("weekly", "low", "2026-02-02", 125, "2026-02-23"),
                ],
                "daily": [
                    _swing("daily", "low", "2026-05-01", 130, "2026-05-15"),
                    _swing("daily", "high", "2026-07-01", 160, "2026-07-15"),
                    _swing("daily", "low", "2026-08-01", 145, daily_confirmed),
                ],
            }
        },
    }


def _bars() -> dict[str, list[dict[str, object]]]:
    dates = {
        "monthly": ["2020-01-01", "2023-01-01", "2024-01-01", "2026-08-01"],
        "weekly": ["2025-01-06", "2025-10-06", "2026-02-02", "2026-08-24"],
        "daily": ["2026-05-01", "2026-07-01", "2026-08-01", "2026-08-25"],
    }
    values: dict[str, list[dict[str, object]]] = {}
    for timeframe, items in dates.items():
        values[timeframe] = [
            {
                "date": date,
                "open": 100 + index * 10,
                "high": 110 + index * 10,
                "low": 90 + index * 10,
                "close": 105 + index * 10,
                "volume": 1_000 + index * 100,
                "trading_value": 100_000 + index * 10_000,
            }
            for index, date in enumerate(items)
        ]
    return values


def _packet(*, future_daily: bool = False, full_debug: bool = False):
    source = build_price_structure_evidence_packet(
        ticker="TEST",
        security_id="security:test",
        currency="USD",
        current_price=150,
        structure=_structure(future_daily=future_daily),
        cutoff="2026-08-25",
        compact=False,
    )
    return build_price_only_ai_anchor_packet(
        source,
        _bars(),
        market="US",
        full_debug=full_debug,
    )


def _output(packet=None) -> VariableAIAnchorOutput:
    packet = packet or _packet()
    reference = reference_select_price_structure(
        build_price_structure_evidence_packet(
            ticker="TEST",
            security_id="security:test",
            currency="USD",
            current_price=150,
            structure=_structure(),
            cutoff="2026-08-25",
            compact=False,
        )
    )
    values = {}
    for timeframe in ("monthly", "weekly", "daily"):
        selected = getattr(reference, timeframe)
        values[timeframe] = VariableTimeframeSelection(
            status=selected.status,
            support_zone_id=selected.support_zone_id,
            resistance_zone_id=selected.resistance_zone_id,
            fib_mode=selected.fib_mode,
            low_pivot_id=selected.low_pivot_id,
            high_pivot_id=selected.high_pivot_id,
            correction_low_pivot_id=selected.correction_low_pivot_id,
            confidence="MEDIUM",
            reason_categories=("MAJOR_BASE",),
            evidence_refs=selected.evidence_refs,
            concise_reason="Canonical price-only structure supports these IDs.",
        )
    return VariableAIAnchorOutput(ticker=packet.ticker, **values)


def test_price_only_packet_is_rich_bounded_and_has_no_fibonacci() -> None:
    packet = _packet()
    payload = packet.model_dump(mode="json")
    audit = audit_price_only_evidence_egress(packet)

    assert packet.contract == PACKET_CONTRACT
    assert packet.evidence_mode == "COMPACT_RICH"
    assert audit["status"] == "PASS"
    assert audit["precomputed_fibonacci_fields"] == 0
    assert "fibonacci" not in str(payload).casefold()
    for timeframe in ("monthly", "weekly", "daily"):
        evidence = getattr(packet, timeframe)
        assert evidence.bars
        assert evidence.candidate_neighborhoods
        assert evidence.swing_segments
        assert all(item.features.range >= 0 for item in evidence.bars)
        assert len(evidence.recent_bar_ids) <= evidence.recent_window_limit


def test_full_debug_preserves_all_bars_and_is_mode_sensitive() -> None:
    compact = _packet()
    full = _packet(full_debug=True)

    assert full.evidence_mode == "FULL_DEBUG"
    assert full.evidence_sha256 != compact.evidence_sha256
    for timeframe in ("monthly", "weekly", "daily"):
        assert len(getattr(full, timeframe).bars) >= len(getattr(compact, timeframe).bars)


def test_valid_variable_output_is_accepted_and_reproducible() -> None:
    packet = _packet()
    output = _output(packet)
    first = execute_variable_anchor_selector(packet, lambda _: output)
    second = execute_variable_anchor_selector(packet, lambda _: output.model_dump(mode="json"))

    assert validate_variable_ai_anchor_output(packet, output).valid is True
    assert first.status == second.status == "PASS"
    assert first.shadow == second.shadow
    assert first.fallback_timeframes == ()


def test_output_schema_rejects_numeric_price_fields_and_long_reason() -> None:
    payload = _output().model_dump(mode="json")
    payload["daily"]["anchor_price"] = 123
    with pytest.raises(ValidationError):
        VariableAIAnchorOutput.model_validate(payload)

    payload = _output().model_dump(mode="json")
    payload["daily"]["concise_reason"] = "x" * 241
    with pytest.raises(ValidationError):
        VariableAIAnchorOutput.model_validate(payload)


def test_ticker_mismatch_rejects_every_timeframe_and_falls_back() -> None:
    packet = _packet()
    output = _output(packet).model_copy(update={"ticker": "OTHER"})
    validation = validate_variable_ai_anchor_output(packet, output)
    result = execute_variable_anchor_selector(packet, lambda _: output)

    assert validation.valid is False
    assert set(validation.timeframe_status.values()) == {"REJECTED"}
    assert result.fallback_timeframes == ("monthly", "weekly", "daily")
    assert all(not result.shadow.selected_fibonacci[key] for key in result.fallback_timeframes)


def test_cross_timeframe_and_alternative_ids_are_rejected_per_slot() -> None:
    packet = _packet()
    output = _output(packet)
    invalid_daily = output.daily.model_copy(
        update={
            "low_pivot_id": output.monthly.low_pivot_id,
            "alternative": AlternativeAnchorSelection(
                low_pivot_id=output.monthly.low_pivot_id,
                high_pivot_id=output.daily.high_pivot_id,
                reason_category="AMBIGUOUS_COMPETING_SWINGS",
            ),
            "evidence_refs": (*output.daily.evidence_refs, output.monthly.low_pivot_id),
        }
    )
    invalid = output.model_copy(update={"daily": invalid_daily})
    result = execute_variable_anchor_selector(packet, lambda _: invalid)

    assert result.validation.timeframe_status["monthly"] == "PASS"
    assert result.validation.timeframe_status["weekly"] == "PASS"
    assert result.validation.timeframe_status["daily"] == "REJECTED"
    assert result.fallback_timeframes == ("daily",)
    assert result.shadow.selected_fibonacci["monthly"]
    assert result.shadow.selected_fibonacci["weekly"]
    assert result.shadow.selected_fibonacci["daily"] == ()


def test_invalid_chronology_is_rejected() -> None:
    packet = _packet()
    output = _output(packet)
    invalid_monthly = output.monthly.model_copy(
        update={
            "low_pivot_id": output.monthly.high_pivot_id,
            "high_pivot_id": output.monthly.low_pivot_id,
        }
    )
    validation = validate_variable_ai_anchor_output(
        packet, output.model_copy(update={"monthly": invalid_monthly})
    )

    assert validation.timeframe_status["monthly"] == "REJECTED"
    assert any("monthly:fib_anchor_kind_invalid" in item for item in validation.errors)


def test_ambiguous_slot_uses_deterministic_sr_without_blocking_packet() -> None:
    packet = _packet()
    output = _output(packet)
    ambiguous = output.model_copy(
        update={
            "daily": VariableTimeframeSelection(
                status="AMBIGUOUS",
                confidence="LOW",
                reason_categories=("AMBIGUOUS_COMPETING_SWINGS",),
                concise_reason="Two tactical swings remain materially competitive.",
            )
        }
    )
    result = execute_variable_anchor_selector(packet, lambda _: ambiguous)

    assert result.status == "PASS"
    assert result.packet_continues is True
    assert result.fallback_timeframes == ("daily",)
    assert result.selection.daily.support_zone_id is not None
    assert result.shadow.selected_fibonacci["daily"] == ()


def test_insufficient_slot_may_cite_valid_sr_but_fallback_stays_deterministic() -> None:
    packet = _packet()
    output = _output(packet)
    omitted = output.model_copy(
        update={
            "daily": VariableTimeframeSelection(
                status="INSUFFICIENT_STRUCTURE",
                support_zone_id=output.daily.support_zone_id,
                resistance_zone_id=output.daily.resistance_zone_id,
                confidence="LOW",
                reason_categories=("AMBIGUOUS_COMPETING_SWINGS",),
                evidence_refs=tuple(
                    ref
                    for ref in (
                        output.daily.support_zone_id,
                        output.daily.resistance_zone_id,
                    )
                    if ref is not None
                ),
                concise_reason="Canonical tactical pivots do not describe the current regime.",
            )
        }
    )
    result = execute_variable_anchor_selector(packet, lambda _: omitted)

    assert result.validation.timeframe_status["daily"] == "OMITTED"
    assert result.fallback_timeframes == ("daily",)
    assert result.selection.daily.support_zone_id is not None
    assert result.shadow.selected_fibonacci["daily"] == ()


@pytest.mark.parametrize(
    "selector",
    (
        lambda _: (_ for _ in ()).throw(TimeoutError()),
        lambda _: (_ for _ in ()).throw(ConnectionError()),
        lambda _: "not-json",
        lambda _: {"contract": "wrong"},
    ),
)
def test_runtime_failure_modes_fail_closed_and_preserve_deterministic_sr(selector) -> None:
    result = execute_variable_anchor_selector(_packet(), selector)

    assert result.status == "FAIL_CLOSED"
    assert result.packet_continues is True
    assert result.fallback_timeframes == ("monthly", "weekly", "daily")
    assert all(getattr(result.selection, key).support_zone_id for key in result.fallback_timeframes)
    assert all(not result.shadow.selected_fibonacci[key] for key in result.fallback_timeframes)


def test_future_unconfirmed_pivot_never_enters_ai_packet() -> None:
    packet = _packet(future_daily=True)

    assert all(item.date != "2026-08-01" for item in packet.daily.pivots)
    assert all(item.confirmed_at <= packet.cutoff for item in packet.daily.pivots)


def test_exact_runs_are_stable() -> None:
    packet = _packet()
    runs = [execute_variable_anchor_selector(packet, lambda _: _output(packet)) for _ in range(3)]
    decision = classify_anchor_stability(packet, runs)

    assert decision.monthly.classification == StabilityClass.STABLE
    assert decision.weekly.classification == StabilityClass.STABLE
    assert decision.daily.classification == StabilityClass.STABLE
    assert decision.user_visible_eligible is True


def _packet_with_extra_low(packet, timeframe: str, *, price: str):
    evidence = getattr(packet, timeframe)
    original = next(item for item in evidence.pivots if item.kind == "low")
    extra = PivotEvidence(
        pivot_id=f"{original.pivot_id}:alternate:{price}",
        ticker=original.ticker,
        timeframe=original.timeframe,
        kind="low",
        date="2020-02-01" if timeframe == "monthly" else "2026-05-02",
        confirmed_at="2020-03-02" if timeframe == "monthly" else "2026-05-16",
        price=Decimal(price),
        adjustment_basis=original.adjustment_basis,
        source_ref=f"{original.source_ref}:alternate",
    )
    return packet.model_copy(
        update={timeframe: evidence.model_copy(update={"pivots": (*evidence.pivots, extra)})}
    ), extra


def _run_with_low(packet, output, timeframe: str, pivot: PivotEvidence):
    selected = getattr(output, timeframe)
    refs = tuple(dict.fromkeys((*selected.evidence_refs, pivot.pivot_id)))
    changed = selected.model_copy(update={"low_pivot_id": pivot.pivot_id, "evidence_refs": refs})
    return execute_variable_anchor_selector(
        packet, lambda _: output.model_copy(update={timeframe: changed})
    )


def test_different_anchor_with_same_visible_structure_is_minor_variation() -> None:
    base = _packet()
    packet, extra = _packet_with_extra_low(base, "monthly", price="50.1")
    output = _output(packet)
    runs = [
        execute_variable_anchor_selector(packet, lambda _: output),
        _run_with_low(packet, output, "monthly", extra),
    ]
    decision = classify_anchor_stability(packet, runs)

    assert decision.monthly.classification == StabilityClass.MINOR_VARIATION
    assert decision.monthly.structure_equivalent is True
    assert decision.user_visible_eligible is True


def test_existing_tolerance_rejects_material_monthly_variation() -> None:
    base = _packet()
    packet, extra = _packet_with_extra_low(base, "monthly", price="80")
    output = _output(packet)
    runs = [
        execute_variable_anchor_selector(packet, lambda _: output),
        _run_with_low(packet, output, "monthly", extra),
    ]
    decision = classify_anchor_stability(packet, runs)

    assert decision.monthly.classification == StabilityClass.MATERIAL_VARIATION
    assert decision.user_visible_eligible is False
    assert "monthly" in decision.timeframe_fib_fallbacks


def test_daily_material_variation_omits_only_daily_fibonacci() -> None:
    base = _packet()
    packet, extra = _packet_with_extra_low(base, "daily", price="140")
    output = _output(packet)
    runs = [
        execute_variable_anchor_selector(packet, lambda _: output),
        _run_with_low(packet, output, "daily", extra),
    ]
    decision = classify_anchor_stability(packet, runs)

    assert decision.daily.classification == StabilityClass.MATERIAL_VARIATION
    assert decision.user_visible_eligible is True
    assert decision.timeframe_fib_fallbacks == ("daily",)


def test_kr_and_us_use_the_same_public_contract() -> None:
    us = _packet()
    kr = us.model_copy(update={"market": "KR", "currency": "KRW"})

    assert set(us.model_dump()) == set(kr.model_dump())
    assert audit_price_only_evidence_egress(kr)["status"] == "PASS"
