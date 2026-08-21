from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.services.kr_investor_flow_service import (
    PARTICIPANT_CONTRACT,
    RECONCILIATION_CONTRACT,
    build_investor_flow_reconciliation,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a read-only KR investor-flow audit.")
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--api-key-env", default="ACTION_API_KEY")
    args = parser.parse_args()

    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise SystemExit(f"missing environment variable: {args.api_key_env}")

    rows = []
    successes = 0
    failures = 0
    for stock in packet.get("stocks", []):
        if not isinstance(stock, dict) or not stock.get("ticker"):
            continue
        ticker = str(stock["ticker"])
        try:
            payload = _fetch(args.base_url, api_key, ticker)
            rows.append(_audit_stock(stock, payload))
            successes += 1
        except Exception as exc:  # pragma: no cover - live evidence boundary
            rows.append({"ticker": ticker, "status": "provider_error", "error": str(exc)})
            failures += 1

    output = {
        "contract": RECONCILIATION_CONTRACT,
        "participant_contract": PARTICIPANT_CONTRACT,
        "packet_id": packet.get("packet_id"),
        "packet_market": packet.get("market"),
        "assessment_date": packet.get("assessment_date"),
        "source_policy": "bounded_read_only_active_packet_universe",
        "provider_calls": {
            "ohlcv_analyst": {
                "requests": successes + failures,
                "successes": successes,
                "failures": failures,
                "cache_hits": "provider_managed_not_observed",
            }
        },
        "summary": _summary(rows),
        "stocks": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _fetch(base_url: str, api_key: str, ticker: str) -> dict[str, Any]:
    query = urlencode(
        {
            "symbol": ticker,
            "market": "KR",
            "periods": "daily",
            "count": 30,
            "include_indicators": "false",
            "include_investor_flows": "true",
        }
    )
    request = Request(
        f"{base_url.rstrip('/')}/ohlcv?{query}",
        headers={"X-API-Key": api_key},
    )
    with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed local URL by default
        return json.load(response)


def _audit_stock(stock: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    daily = payload.get("periods", {}).get("daily", [])
    source_signal = payload.get("supply_demand", {}).get("primary_signal")
    result = build_investor_flow_reconciliation(
        daily,
        provider_primary_signal=source_signal,
    )
    packet_supply = stock.get("price_and_positioning", {}).get("supply", {})
    windows = {
        key: value.model_dump(mode="json")
        for key, value in result.get("reconciliations", {}).items()
    }
    preserved = {}
    for suffix in ("", "_5", "_20"):
        window = {"": "1d", "_5": "5d", "_20": "20d"}[suffix]
        reconciliation = windows.get(window, {})
        flows = reconciliation.get("participant_flows", {})
        for participant, field in (
            ("foreign", "foreign_net_buy_qty"),
            ("institution", "institution_net_buy_qty"),
            ("individual", "individual_net_buy_qty"),
        ):
            packet_value = packet_supply.get(f"{field}{suffix}")
            source_value = flows.get(participant)
            preserved[f"{participant}_{window}"] = {
                "packet": packet_value,
                "source": source_value,
                "preserved": packet_value == source_value,
            }
    after_signal = result.get("primary_signal")
    return {
        "ticker": stock.get("ticker"),
        "company_name": stock.get("company_name"),
        "status": "audited",
        "provider": payload.get("meta", {}).get("provider"),
        "provider_generated_at": payload.get("meta", {}).get("generated_at"),
        "provider_primary_signal": source_signal,
        "canonical_primary_signal": after_signal,
        "signal_basis_window": result.get("signal_basis_window"),
        "attribution_safe": result.get("attribution_safe"),
        "attribution_confidence": result.get("attribution_confidence"),
        "omitted_participant_materiality": result.get("omitted_participant_materiality"),
        "participant_taxonomy": [
            item.model_dump(mode="json") for item in result.get("participant_taxonomy", [])
        ],
        "windows": windows,
        "diagnostic_subcomponents": result.get("diagnostic_subcomponents", {}),
        "institution_subclass_difference": result.get("institution_subclass_difference", {}),
        "displayed_three_preservation": preserved,
        "packet_vs_later_source_equal": all(item["preserved"] for item in preserved.values()),
        "source_occurrence_drift": not all(
            item["preserved"] for item in preserved.values()
        ),
        "implementation_numeric_transform": "identity",
        "unsupported_attribution_before": bool(
            source_signal
            in {
                "foreign_exit_retail_absorption",
                "foreign_exit_institution_retail_absorption",
            }
            and not result.get("attribution_safe")
        ),
        "unsupported_attribution_after": bool(
            after_signal
            in {
                "foreign_exit_retail_absorption",
                "foreign_exit_institution_retail_absorption",
            }
            and not result.get("attribution_safe")
        ),
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    audited = [row for row in rows if row.get("status") == "audited"]
    return {
        "ticker_count": len(rows),
        "audited": len(audited),
        "provider_errors": len(rows) - len(audited),
        "complete_windows": sum(
            window.get("reconciliation_status") == "complete_without_provider_total"
            for row in audited
            for window in row.get("windows", {}).values()
        ),
        "window_count": len(audited) * 3,
        "material_omitted_windows": sum(
            bool(window.get("material_omitted_flow"))
            for row in audited
            for window in row.get("windows", {}).values()
        ),
        "unsupported_attribution_before": sum(
            bool(row.get("unsupported_attribution_before")) for row in audited
        ),
        "unsupported_attribution_after": sum(
            bool(row.get("unsupported_attribution_after")) for row in audited
        ),
        "implementation_numeric_identity": True,
        "stable_source_occurrence_tickers": sum(
            bool(row.get("packet_vs_later_source_equal")) for row in audited
        ),
        "later_source_occurrence_drift_tickers": [
            row.get("ticker")
            for row in audited
            if row.get("source_occurrence_drift")
        ],
        "sk_hynix_packet_vs_source_equal": all(
            bool(row.get("packet_vs_later_source_equal"))
            for row in audited
            if row.get("ticker") == "000660"
        ),
    }


if __name__ == "__main__":
    main()
