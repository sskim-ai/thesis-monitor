"""Offline, consumer-scoped stock source projection. Not a complete Core packet.

Integrity facts are immutable. Eligibility is a separate consumer verdict. No
live acquisition, renderer, database, or previous assessment is an input here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.services.ohlcv_feature_engine_service import _feature_facts, _normalize_bars
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.ohlcv_structure_service import (
    LOCAL_CONFIG, LOCAL_PIVOT_LOOKBACKS, MAJOR_CONFIG, normalize_structure_bars,
)
from app.services.packet_owned_technical_context_service import build_packet_owned_technical_context
from app.services.price_structure_wave_fibonacci_v3_service import HISTORY_REQUESTS, prepare_long_history
from app.services.unified_snapshot_contract import digest


CONTRACT = "stock-consumer-anomaly-scope-v1"
_RELATION_FIELDS = {
    "HIGH_LT_OPEN": {"high", "open"}, "HIGH_LT_CLOSE": {"high", "close"},
    "LOW_GT_OPEN": {"low", "open"}, "LOW_GT_CLOSE": {"low", "close"},
    "LOW_GT_HIGH": {"low", "high"}, "NEGATIVE_VOLUME": {"volume"},
}
_STRUCTURAL = {"INVALID_BAR_DATE", "FUTURE_BAR", "DUPLICATE_TIMESTAMP",
               "DUPLICATE_CONFLICT", "BAR_TIMESTAMP_ORDERING"}


@dataclass(frozen=True)
class ConsumerRows:
    consumer: str
    owner: str
    selection: str
    dates: tuple[str, ...] | None
    fields: frozenset[str]
    requirement: Literal["MANDATORY_CURRENT_PRICE", "OPTIONAL_COMPONENT", "UNRESOLVED"]
    # Existing normalizers drop malformed rows. A date span records those holes
    # as dependencies, never as an authorization to remove bad data.
    dependency_span: tuple[str, str] | None = None
    existing_row_integrity_prerequisite: bool = False


def assess_consumer(rows: list[dict], *, timeframe: str, cutoff: date,
                    consumer: ConsumerRows) -> dict:
    inspection = inspect_normalized_ohlcv_rows(rows, timeframe=timeframe, cutoff=cutoff)
    observed_dates = [str(row.get("date") or "")[:10] for row in rows]
    latest = max(observed_dates, default=None)
    current_bad = bool(latest and any(issue.bar_date == latest for issue in inspection.issues))
    unknown = consumer.dates is None or any(
        issue.violation.value in _STRUCTURAL for issue in inspection.issues)
    issues = []
    relevant = []
    for issue in inspection.issues:
        row_used = consumer.dates is not None and issue.bar_date in consumer.dates
        if consumer.dependency_span and issue.bar_date:
            row_used |= consumer.dependency_span[0] <= issue.bar_date <= consumer.dependency_span[1]
        fields_used = (consumer.existing_row_integrity_prerequisite or
            bool(consumer.fields & _RELATION_FIELDS.get(issue.violation.value, consumer.fields)))
        relevance = "UNKNOWN" if unknown else "CONSUMED" if row_used else "NOT_CONSUMED"
        item = {**issue.model_dump(mode="json"), "row_relevance": relevance,
                "affected_fields_required": fields_used,
                "blocks_consumer": unknown or (row_used and fields_used)}
        issues.append(item)
        if item["blocks_consumer"]:
            relevant.append(item)
    if not rows:
        reason = "SOURCE_ROWS_UNAVAILABLE"
    elif current_bad:
        reason = "CURRENT_SNAPSHOT_SOURCE_ANOMALY"
    elif unknown:
        reason = "SOURCE_ANOMALY_RELEVANCE_UNKNOWN"
    elif relevant:
        reason = "SOURCE_ANOMALY_RELEVANT_TO_CONSUMER"
    elif not consumer.dates:
        reason = "CONSUMER_ROWS_UNAVAILABLE"
    elif inspection.issues:
        reason = ("SOURCE_ANOMALY_PRESERVED_UNUSED_FIELDS" if any(
            item["row_relevance"] == "CONSUMED" for item in issues)
            else "SOURCE_ANOMALY_PRESERVED_OUTSIDE_CONSUMED_WINDOW")
    else:
        reason = "VALID"
    eligible = reason in {"VALID", "SOURCE_ANOMALY_PRESERVED_UNUSED_FIELDS",
                          "SOURCE_ANOMALY_PRESERVED_OUTSIDE_CONSUMED_WINDOW"}
    return {"consumer": consumer.consumer, "owner": consumer.owner,
            "selection": consumer.selection, "required_fields": sorted(consumer.fields),
            "requirement": consumer.requirement, "selected_dates": consumer.dates,
            "dependency_span": consumer.dependency_span,
            "existing_row_integrity_prerequisite": consumer.existing_row_integrity_prerequisite,
            "source_integrity": "VALID" if inspection.valid else "SOURCE_ANOMALY_PRESERVED",
            "source_fingerprint": inspection.payload_fingerprint, "row_count": len(rows),
            "latest_date": latest, "latest_row_valid": bool(rows) and not current_bad and not unknown,
            "anomalies": issues, "eligible": eligible, "reason": reason}


def _dates(rows) -> tuple[str, ...]:
    return tuple(str(row["date"])[:10] for row in rows)


def _structure_consumer(rows, timeframe, kind, *, cutoff, market, observed_at):
    if kind == "v3_long_cycle":
        selected, _ = prepare_long_history(rows, timeframe=timeframe, cutoff=cutoff.isoformat(),
            adjustment_basis="provider_adjusted_price_v1", market=market.upper(),
            observed_at=observed_at, provider_limit=1000)
        owner = "price_structure_wave_fibonacci_v3_service.prepare_long_history"
        rule = f"complete[-{HISTORY_REQUESTS[timeframe]}:] + partial; calendar finality"
        selection = tuple(bar.date for bar in selected)
    else:
        count = {"legacy_local_pivots": LOCAL_PIVOT_LOOKBACKS[timeframe],
                 "legacy_major_swings_atr": MAJOR_CONFIG[timeframe].lookback,
                 "legacy_boxes": LOCAL_CONFIG[timeframe].box_lookback}[kind]
        selected = normalize_structure_bars(rows, lookback=count)
        owner = "ohlcv_structure_service." + {
            "legacy_local_pivots": "detect_local_pivots", "legacy_boxes": "detect_boxes",
            "legacy_major_swings_atr": "normalize_bar_series / calc_wilder_atr / analyze_chart_structure",
        }[kind]
        rule = f"existing normalize_structure_bars sorted tail[-{count}:]"
        selection = tuple(bar.date for bar in selected)
    # Include malformed holes inside the real selected range, including leading
    # malformed rows when the owner requests the complete available history.
    requested = HISTORY_REQUESTS[timeframe] if kind == "v3_long_cycle" else count
    candidates = _dates(rows[-requested:])
    span_dates = (*selection, *candidates)
    return ConsumerRows(kind, owner, rule, selection,
        frozenset({"date", "open", "high", "low", "close", "volume"}),
        "OPTIONAL_COMPONENT", (min(span_dates), max(span_dates)) if span_dates else None, True)


def role_consumers(rows: list[dict], *, role: str, timeframe: str, cutoff: date,
                   market: str, observed_at: str) -> list[dict]:
    consumers = []
    if role == "unadjusted_weekly_valuation":
        consumers.append(ConsumerRows("valuation_weekly_close_history",
            "ohlcv_client.fetch_price_context / historical_valuation_service._weekly_prices",
            "all returned rows -> HistoricalPricePoint(date, close); weekly PIT denominators later",
            _dates(rows), frozenset({"date", "close"}), "OPTIONAL_COMPONENT"))
    else:
        consumers.extend([
            ConsumerRows("current_price" if timeframe == "daily" else "latest_close",
                "ohlcv_client._summarize_bars / fetch_price_context.PriceDecisionContext",
                "bars[-1].close", _dates(rows[-1:]), frozenset({"date", "close"}),
                "MANDATORY_CURRENT_PRICE" if timeframe == "daily" else "OPTIONAL_COMPONENT"),
            ConsumerRows("period_range_position", "ohlcv_client._summarize_bars",
                "min(low), max(high) of all returned rows; latest close", _dates(rows),
                frozenset({"date", "low", "high", "close"}), "OPTIONAL_COMPONENT"),
            ConsumerRows("latest_candle_volume_value", "ohlcv_client._chart_timeframe_context",
                "bars[-1] OHLC/body/wicks/volume/value (not embedded indicator dependencies)",
                _dates(rows[-1:]), frozenset({"date", "open", "high", "low", "close", "volume", "value"}),
                "OPTIONAL_COMPONENT"),
        ])
        for kind in ("legacy_local_pivots", "legacy_major_swings_atr", "legacy_boxes", "v3_long_cycle"):
            consumers.append(_structure_consumer(rows, timeframe, kind, cutoff=cutoff,
                market=market, observed_at=observed_at))
        # A boxes output also consumes pivot-derived zones, not only recent bars.
        local = next(c for c in consumers if c.consumer == "legacy_local_pivots")
        boxes_index = next(i for i, c in enumerate(consumers) if c.consumer == "legacy_boxes")
        boxes = consumers[boxes_index]
        consumers[boxes_index] = ConsumerRows(boxes.consumer, boxes.owner,
            boxes.selection + "; plus local-pivot zones", tuple(sorted(set((*boxes.dates, *local.dates)))),
            boxes.fields, boxes.requirement, local.dependency_span, True)
    results = [assess_consumer(rows, timeframe=timeframe, cutoff=cutoff, consumer=c) for c in consumers]
    for result in results:
        if (result["consumer"] == "current_price" and result["eligible"]
                and result["latest_date"] != cutoff.isoformat()):
            result.update(eligible=False, reason="CURRENT_SESSION_MISMATCH")
    return results


def materialize_source_components(*, ticker: str, market: str, cutoff: date,
                                 observed_at: str, roles: dict[str, list[dict]]) -> dict:
    """Actual typed feature projection, without inventing a financial/Core owner.

    The complete stock adapter has not been implemented by R2A-R5/R2B0. This
    function deliberately cannot qualify a Core/A/B packet on OHLCV alone.
    """
    expected = {"adjusted_daily", "adjusted_weekly", "adjusted_monthly", "unadjusted_weekly_valuation"}
    if set(roles) != expected:
        raise ValueError("exact_four_owned_roles_required")
    before = digest(roles)
    matrix = {}
    for role, rows in roles.items():
        timeframe = "weekly" if role == "unadjusted_weekly_valuation" else role.removeprefix("adjusted_")
        matrix[role] = role_consumers(rows, role=role, timeframe=timeframe, cutoff=cutoff,
            market=market, observed_at=observed_at)
    current = matrix["adjusted_daily"][0]
    periods = {tf: roles[f"adjusted_{tf}"] for tf in ("daily", "weekly", "monthly")}
    context = build_packet_owned_technical_context(ticker=ticker, market=market, session="closed",
        as_of=observed_at, periods=periods, cutoff=cutoff, expected_daily_completed=cutoff.isoformat(),
        source="sealed_r2b0_kiwoom", source_version="one-shot-stock-source-acquisition-v1")
    # The existing feature owner may retain historical features when the latest
    # row is bad. Those must not become current-snapshot inputs in this adapter.
    features = {}
    for tf in periods:
        quality = context.quality[{"daily": "D", "weekly": "W", "monthly": "M"}[tf]]
        role_current_ok = matrix[f"adjusted_{tf}"][0]["latest_row_valid"]
        feature_set = getattr(context.features, tf)
        dependencies = []
        normalized = _normalize_bars(periods[tf], cutoff)
        _feature_facts(ticker, tf, normalized.bars, "adjusted_close", normalized.invalid_dates,
            dependency_audit=dependencies)
        feature_consumers = []
        for dep in dependencies:
            start, end = dep["dependency_start"], dep["dependency_end"]
            dates = tuple(bar.as_of.isoformat() for bar in normalized.bars
                if start and end and start <= bar.as_of.isoformat() <= end)
            verdict = assess_consumer(periods[tf], timeframe=tf, cutoff=cutoff,
                consumer=ConsumerRows(str(dep["semantic"]),
                    "ohlcv_feature_engine_service._feature_facts / technical_feature_dependency_service.assess_feature_dependency",
                    f'{dep["dependency_kind"]}; minimum_history={dep["required_bars"]}', dates,
                    frozenset({"date", "open", "high", "low", "close", "volume"}),
                    "OPTIONAL_COMPONENT", (start, end) if start and end else None, True))
            feature_consumers.append({**verdict, "owner_dependency": dep})
        allowed = {c["consumer"] for c in feature_consumers if c["eligible"]}
        features[tf] = {"quality": quality.model_dump(mode="json"),
            "facts": [fact.model_dump(mode="json") for fact in feature_set.facts if fact.semantic in allowed]
                if role_current_ok and quality.usable_for_current_reasoning else [],
            "owner_blocked_features": list(feature_set.blocked_features),
            "source_invalid_rows": list(feature_set.invalid_source_rows),
            "current_role_gate": role_current_ok,
            "suppression_reason": None if role_current_ok and quality.usable_for_current_reasoning
                else "CURRENT_ROLE_OR_FRESHNESS_BLOCKED"}
        matrix[f"adjusted_{tf}"].extend(feature_consumers)
    if digest(roles) != before:
        raise ValueError("source_rows_mutated")
    components = {"contract": CONTRACT, "ticker": ticker, "market": market,
        "cutoff": cutoff.isoformat(), "source_rows_sha256": before,
        "current_price": roles["adjusted_daily"][-1]["close"] if current["eligible"] else None,
        "current_price_eligible": current["eligible"], "role_consumer_matrix": matrix,
        "technical_context_id": context.technical_context_id,
        "technical_status": context.status.value, "features": features,
        "complete_stock_packet": False, "stock_packet_sha256": None,
        "materializer_status": "BLOCKED_COMPLETE_STOCK_OWNER_NOT_IMPLEMENTED",
        "observed_business_union_status": "NOT_REACHED_NO_BOUND_CLASS_C_INPUT",
        "mandatory_current_price_failure": not current["eligible"],
        "component_projection_sha256": None}
    components["component_projection_sha256"] = digest(components)
    return components
