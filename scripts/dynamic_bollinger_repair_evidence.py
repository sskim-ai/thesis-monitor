from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from app.services.kr_price_structure_selective_rollout_service import (
    apply_current_price_structure_section,
    build_kr_price_structure_rollout_decision,
    build_kr_price_structure_runtime_context,
    suppress_current_price_structure_surface,
)
from app.services.ohlcv_client import OHLCV_PROVIDER_REQUEST_LIMIT
from app.services.us_price_structure_selective_rollout_service import (
    build_us_price_structure_rollout_decision,
    build_us_price_structure_runtime_context,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "dynamic-bollinger-layer-repair-evidence-v1"
NAMESPACE = "TEST_ONLY_DYNAMIC_BOLLINGER_LAYER_REPAIR"
DYNAMIC_SEMANTICS = {
    "DYNAMIC_BOLLINGER_SUPPORT",
    "DYNAMIC_BOLLINGER_RESISTANCE",
}
MAJOR_SEMANTICS = {"MAJOR_SUPPORT", "MAJOR_RESISTANCE"}
VISIBLE_SR_SEMANTICS = {
    "NEAR_SUPPORT",
    "NEAR_RESISTANCE",
    "MAJOR_SUPPORT",
    "MAJOR_RESISTANCE",
    "LONG_HORIZON_SUPPORT",
    "LONG_HORIZON_RESISTANCE",
    *DYNAMIC_SEMANTICS,
}


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rows_by_ticker(payload: object, key: str) -> dict[str, Mapping[str, object]]:
    if not isinstance(payload, Mapping) or not isinstance(payload.get(key), list):
        raise ValueError(f"invalid evidence bundle key: {key}")
    return {
        str(row.get("ticker")): row
        for row in payload[key]
        if isinstance(row, Mapping) and row.get("ticker")
    }


def _zone(summary: Mapping[str, object], key: str) -> Mapping[str, object] | None:
    value = summary.get(key)
    if key.startswith("dynamic_bollinger_"):
        return value if isinstance(value, Mapping) else None
    if not isinstance(value, Mapping):
        return None
    zone = value.get("zone")
    return zone if isinstance(zone, Mapping) else None


def _zone_audit(zone: Mapping[str, object] | None) -> dict[str, object]:
    if zone is None:
        return {
            "visible": False,
            "zone_id": None,
            "display": None,
            "source_timeframe": None,
            "source_families": [],
            "source_refs": [],
            "price_anchor_refs": [],
            "indicator_observation_dates": [],
            "indicator_bar_states": [],
            "proximity_tier": None,
            "active_relevance": None,
        }
    return {
        "visible": True,
        "zone_id": zone.get("zone_id"),
        "display": zone.get("display"),
        "source_timeframe": zone.get("source_timeframe"),
        "source_families": list(zone.get("source_families") or ()),
        "source_refs": list(zone.get("source_refs") or ()),
        "price_anchor_refs": list(zone.get("price_anchor_refs") or ()),
        "indicator_observation_dates": list(
            zone.get("indicator_observation_dates") or ()
        ),
        "indicator_bar_states": list(zone.get("indicator_bar_states") or ()),
        "proximity_tier": zone.get("proximity_tier"),
        "active_relevance": zone.get("active_relevance"),
    }


def _message_with_section(message: str, section: str | None) -> str:
    if section:
        return apply_current_price_structure_section(message, section)
    return suppress_current_price_structure_surface(message)


def _invalid_ohlc_rows(raw_by_timeframe: Mapping[str, object]) -> list[dict[str, object]]:
    invalid: list[dict[str, object]] = []
    for timeframe, values in raw_by_timeframe.items():
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            continue
        for item in values:
            if not isinstance(item, Mapping):
                continue
            try:
                opening = float(item["open"])
                high = float(item["high"])
                low = float(item["low"])
                close = float(item["close"])
            except (KeyError, TypeError, ValueError):
                continue
            if high < low or not low <= opening <= high or not low <= close <= high:
                invalid.append(
                    {
                        "timeframe": timeframe,
                        "date": item.get("date"),
                        "open": opening,
                        "high": high,
                        "low": low,
                        "close": close,
                    }
                )
    return invalid


def _snapshot(args: argparse.Namespace) -> None:
    raw_payload = _read_json(args.raw_input)
    baseline_payload = _read_json(args.baseline_input)
    raw_subjects = _rows_by_ticker(raw_payload, "subjects")
    baseline_rows = _rows_by_ticker(baseline_payload, "rows")
    observed_at = str(
        raw_payload.get("observed_at")
        if isinstance(raw_payload, Mapping)
        else args.observed_at
    )
    rows: list[dict[str, object]] = []
    messages: list[dict[str, object]] = []
    for ticker in sorted(raw_subjects):
        raw_subject = raw_subjects[ticker]
        baseline = baseline_rows.get(ticker)
        if baseline is None:
            raise ValueError(f"baseline row missing: {ticker}")
        market = str(raw_subject.get("market") or ("KR" if ticker.isdigit() else "US"))
        raw_by_timeframe = raw_subject.get("raw_by_timeframe")
        if not isinstance(raw_by_timeframe, Mapping):
            raise ValueError(f"raw timeframes missing: {ticker}")
        runtime_builder = (
            build_kr_price_structure_runtime_context
            if market == "KR"
            else build_us_price_structure_runtime_context
        )
        structure = runtime_builder(
            ticker=ticker,
            cutoff=str(raw_subject.get("cutoff") or ""),
            raw_by_timeframe=raw_by_timeframe,  # type: ignore[arg-type]
            observed_at=observed_at,
            provider_limit=OHLCV_PROVIDER_REQUEST_LIMIT,
        )
        decision_builder = (
            build_kr_price_structure_rollout_decision
            if market == "KR"
            else build_us_price_structure_rollout_decision
        )
        decision = decision_builder(
            structure,
            ticker=ticker,
            monitored_subject=True,
            enabled=True,
        )
        ai = _message_with_section(str(baseline.get("ai_preview") or ""), decision.section)
        fallback = _message_with_section(
            str(baseline.get("fallback_preview") or ""), decision.section
        )
        route = str(baseline.get("route") or "AI")
        selected = fallback if "FALLBACK" in route.upper() else ai
        summary = structure.get("summary")
        summary = summary if isinstance(summary, Mapping) else {}
        bindings = [dict(value) for value in decision.numeric_bindings]
        dynamic_bindings = [
            value
            for value in bindings
            if str(value.get("semantic_type")) in DYNAMIC_SEMANTICS
        ]
        confluence_bindings = [
            value
            for value in bindings
            if value.get("dynamic_bollinger_confluence") is True
        ]
        major_bindings = [
            value
            for value in bindings
            if str(value.get("semantic_type")) in MAJOR_SEMANTICS
        ]
        major_without_anchor = sum(
            not bool(value.get("price_anchor_refs")) for value in major_bindings
        )
        bollinger_only_major = sum(
            bool(value.get("source_families"))
            and all(
                str(family).startswith("BOLLINGER_")
                for family in value.get("source_families") or ()
            )
            for value in major_bindings
        )
        visible_displays = [
            str(value.get("display") or "")
            for value in bindings
            if str(value.get("semantic_type")) in VISIBLE_SR_SEMANTICS
            and value.get("display")
        ]
        duplicate_ranges = len(visible_displays) - len(set(visible_displays))
        dynamic_evidence_bindings = [*dynamic_bindings, *confluence_bindings]
        dynamic_partial_or_unknown = sum(
            tuple(
                value.get("indicator_bar_states")
                or value.get("dynamic_bollinger_indicator_bar_states")
                or ()
            )
            != ("COMPLETE",)
            for value in dynamic_evidence_bindings
        )
        dynamic_security_basis_conflicts = sum(
            value.get("security_basis") != structure.get("security_basis")
            for value in dynamic_evidence_bindings
        )
        dynamic_adjustment_basis_conflicts = sum(
            value.get("adjustment_basis") != structure.get("adjustment_basis")
            for value in dynamic_evidence_bindings
        )
        dynamic_currency_conflicts = sum(
            value.get("currency") != structure.get("currency")
            for value in dynamic_evidence_bindings
        )
        section = decision.section or ""
        dynamic_support_lines = section.count("• 볼린저 지지(")
        dynamic_resistance_lines = section.count("• 볼린저 저항(")
        dynamic_labels = [
            line
            for line in section.splitlines()
            if "볼린저" in line
        ]
        parity = all(line in ai and line in fallback for line in dynamic_labels)
        invalid_ohlc = _invalid_ohlc_rows(raw_by_timeframe)
        row = {
            "ticker": ticker,
            "company": raw_subject.get("company"),
            "market": market,
            "as_of": structure.get("as_of"),
            "current_price": structure.get("current_price"),
            "currency": structure.get("currency"),
            "security_basis": structure.get("security_basis"),
            "adjustment_basis": structure.get("adjustment_basis"),
            "coverage": structure.get("coverage"),
            "eligibility": decision.eligibility.value,
            "denial_reasons": list(decision.denial_reasons),
            "near_support": _zone_audit(_zone(summary, "nearest_support")),
            "near_resistance": _zone_audit(_zone(summary, "nearest_resistance")),
            "major_support": _zone_audit(
                _zone(summary, "major_structural_support")
            ),
            "major_resistance": _zone_audit(
                _zone(summary, "major_structural_resistance")
            ),
            "dynamic_bollinger_support": _zone_audit(
                _zone(summary, "dynamic_bollinger_support")
            ),
            "dynamic_bollinger_resistance": _zone_audit(
                _zone(summary, "dynamic_bollinger_resistance")
            ),
            "dynamic_bindings": dynamic_bindings,
            "dynamic_confluence_bindings": confluence_bindings,
            "numeric_bindings": bindings,
            "section": decision.section,
            "dynamic_support_line_count": dynamic_support_lines,
            "dynamic_resistance_line_count": dynamic_resistance_lines,
            "major_without_price_anchor": major_without_anchor,
            "bollinger_only_major_visible": bollinger_only_major,
            "duplicate_sr_range_visible": duplicate_ranges,
            "dynamic_partial_or_unknown_bar_visible": dynamic_partial_or_unknown,
            "dynamic_security_basis_conflicts": dynamic_security_basis_conflicts,
            "dynamic_adjustment_basis_conflicts": dynamic_adjustment_basis_conflicts,
            "dynamic_currency_conflicts": dynamic_currency_conflicts,
            "dynamic_ai_fallback_parity": parity,
            "render_validation_errors": list(decision.render_validation_errors),
            "invalid_ohlc_rows": invalid_ohlc,
            "ai_preview": ai,
            "fallback_preview": fallback,
            "selected_preview": selected,
            "selected_sha256": _sha(selected),
            "route": route,
            "unsupported_target": int("목표 가격" in section),
            "unsupported_stop": int("손절" in section),
        }
        row["status"] = "PASS" if all(
            (
                not row["render_validation_errors"],
                major_without_anchor == 0,
                bollinger_only_major == 0,
                duplicate_ranges == 0,
                dynamic_partial_or_unknown == 0,
                dynamic_security_basis_conflicts == 0,
                dynamic_adjustment_basis_conflicts == 0,
                dynamic_currency_conflicts == 0,
                dynamic_support_lines <= 1,
                dynamic_resistance_lines <= 1,
                parity,
                row["unsupported_target"] == 0,
                row["unsupported_stop"] == 0,
            )
        ) else "FAIL"
        rows.append(row)
        messages.append(
            {
                "ticker": ticker,
                "route": route,
                "text": selected,
                "logical_identity": (
                    f"{NAMESPACE}:{ticker}:{structure.get('as_of')}"
                ),
            }
        )
    failed = [row["ticker"] for row in rows if row["status"] != "PASS"]
    output = {
        "contract": CONTRACT,
        "observed_at": observed_at,
        "raw_source": str(args.raw_input),
        "raw_source_sha256": hashlib.sha256(args.raw_input.read_bytes()).hexdigest(),
        "baseline_source": str(args.baseline_input),
        "baseline_source_sha256": hashlib.sha256(
            args.baseline_input.read_bytes()
        ).hexdigest(),
        "universe_count": len(rows),
        "us_count": sum(row["market"] == "US" for row in rows),
        "kr_count": sum(row["market"] == "KR" for row in rows),
        "rows": rows,
        "messages": messages,
        "failed_tickers": failed,
        "status": "PASS" if not failed else "FAIL",
        "provider_calls": {
            "local_ohlcv_analyst_requests": 0,
            "cache_hit_subjects": len(rows),
            "failed_subjects": 0,
        },
    }
    _write_json(args.output, output)
    print(
        json.dumps(
            {
                "status": output["status"],
                "universe_count": len(rows),
                "failed_tickers": failed,
            },
            sort_keys=True,
        )
    )


async def _send(args: argparse.Namespace) -> None:
    payload = _read_json(args.input)
    if not isinstance(payload, Mapping) or payload.get("status") != "PASS":
        raise ValueError("replay evidence is not PASS")
    messages = payload.get("messages")
    if not isinstance(messages, list) or len(messages) != 20:
        raise ValueError("expected exact 20-subject test payload")
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test sink unavailable: {sink.get('reason')}")
    selected_key = str(sink.get("selected_test_key_name") or "")
    receipt = await deliver_test_messages(
        messages,
        token=env.get("TELEGRAM_BOT_TOKEN") or "",
        test_chat_id=env.get(selected_key) or "",
        production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.receipt,
        contract="dynamic-bollinger-layer-test-delivery-v1",
        namespace=NAMESPACE,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "sent_message_count": receipt["sent_message_count"],
                "exact_payload_match": receipt["exact_payload_match"],
                "test_sink_alias": sink["test_sink_alias"],
                "production_sink_alias": sink["production_sink_alias"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    snapshot = subparsers.add_parser("snapshot")
    snapshot.add_argument("--raw-input", type=Path, required=True)
    snapshot.add_argument("--baseline-input", type=Path, required=True)
    snapshot.add_argument("--observed-at")
    snapshot.add_argument("--output", type=Path, required=True)
    send = subparsers.add_parser("send-test")
    send.add_argument("--input", type=Path, required=True)
    send.add_argument("--env-file", type=Path, required=True)
    send.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "snapshot":
        _snapshot(args)
    else:
        asyncio.run(_send(args))


if __name__ == "__main__":
    main()
