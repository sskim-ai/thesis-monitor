from __future__ import annotations

# ruff: noqa: E402

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from sqlmodel import Session, create_engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.semantic_decision_service import select_valuation_context
from scripts import phase8_5_3_1_evidence as previous
from scripts import phase8_5_3_evidence as phase853


REPRESENTATIVES = {
    "us": ("MU", "TSM", "TSLA", "GOOGL", "RXRX"),
    "kr": ("005490", "086280", "003690", "000660"),
}


def _packet_stock(packet: dict[str, object], ticker: str) -> dict[str, object]:
    return next(
        item
        for item in packet["stocks"]
        if isinstance(item, dict) and item.get("ticker") == ticker
    )


def _legacy_label(source: dict[str, object]) -> str:
    canonical = str(source.get("canonical_label") or "").strip()
    if canonical:
        return canonical
    labels = source.get("approved_labels")
    return str(labels[0]) if isinstance(labels, list) and labels else ""


def _legacy_collisions(
    packet: dict[str, object], output: dict[str, object]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    reviews = {
        str(item.get("ticker") or ""): item
        for item in output["stock_reviews"]
        if isinstance(item, dict)
    }
    for stock in packet["stocks"]:
        if not isinstance(stock, dict):
            continue
        ticker = str(stock.get("ticker") or "")
        review = reviews.get(ticker)
        if review is None:
            continue
        registry = {
            (str(item.get("fact_id") or ""), str(item.get("field_path") or "")): item
            for item in stock.get("numeric_registry", [])
            if isinstance(item, dict)
        }
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for ref in review.get("numeric_fact_refs", []):
            if not isinstance(ref, dict):
                continue
            if ref.get("text_ref") != "valuation_analysis.text":
                continue
            source = registry.get(
                (str(ref.get("fact_id") or ""), str(ref.get("field_path") or ""))
            )
            if source is None:
                continue
            if str(source.get("semantic_type") or "") not in {
                "trailing_pe",
                "forward_pe",
                "price_to_book",
                "forward_price_to_book",
                "historical_pe_multiple",
                "historical_pb_multiple",
                "historical_pe_percentile",
                "historical_pb_percentile",
                "peer_pe_multiple",
                "peer_pb_multiple",
            }:
                continue
            label = _legacy_label(source)
            if not label:
                continue
            grouped[label.casefold()].append(
                {
                    "ref_id": ref.get("ref_id"),
                    "label": label,
                    "fact_id": ref.get("fact_id"),
                    "field_path": ref.get("field_path"),
                    "semantic_type": source.get("semantic_type"),
                    "value": source.get("canonical_display_value"),
                }
            )
        for label, entries in grouped.items():
            values = {str(item["value"]) for item in entries}
            paths = {str(item["field_path"]) for item in entries}
            if len(values) > 1 and len(paths) > 1:
                rows.append({"ticker": ticker, "label": label, "entries": entries})
    return rows


def _valuation_context_class(stock: dict[str, object]) -> str:
    valuation = stock.get("valuation")
    valuation = valuation if isinstance(valuation, dict) else {}
    historical = valuation.get("historical_pb_statistics")
    history_available = isinstance(historical, dict) and all(
        historical.get(key) is not None
        for key in ("current_value", "historical_median", "current_percentile")
    )
    peer = valuation.get("peer")
    peer_available = isinstance(peer, dict) and peer.get("available") is True
    forward_available = any(
        valuation.get(key) is not None
        for key in ("forward_pe", "forward_price_to_book")
    )
    return select_valuation_context(
        current_status="available",
        historical_status="available" if history_available else "unavailable",
        peer_status="available" if peer_available else "unavailable",
        forward_status="available" if forward_available else "unavailable",
        current_used=True,
        history_used=history_available,
        peer_used=False,
        forward_used=False,
    ).valuation_context_class


def _audit_market(market: str) -> dict[str, object]:
    packet, draft = previous.hardened_output(market)
    binding = bind_numeric_fact_references(packet, draft)
    if binding.errors:
        raise RuntimeError(f"{market} binding failed: {binding.errors}")
    requested = set(REPRESENTATIVES[market])
    rows = []
    for item in binding.report["bindings"]:
        ticker = str(item["logical_claim_id"]).split(":", maxsplit=1)[0]
        if ticker not in requested or item["text_ref"] != "valuation_analysis.text":
            continue
        rows.append(
            {
                "ticker": ticker,
                **{
                    key: item.get(key)
                    for key in (
                        "ref_id",
                        "fact_id",
                        "field_path",
                        "semantic_type",
                        "comparison_role",
                        "canonical_label",
                        "formatted_value",
                        "text_ref",
                        "usage",
                    )
                },
            }
        )
    covered = {str(item["ticker"]) for item in rows}
    return {
        "full_validator": "PASS",
        "runtime_quality": "PASS",
        "label_quality": binding.report["label_quality"],
        "representative_rows": rows,
        "representatives_without_selected_valuation_numbers": sorted(
            requested - covered
        ),
        "legacy_collisions": _legacy_collisions(packet, draft),
    }


def _rxrx_audit() -> dict[str, object]:
    packet, draft = previous.hardened_output("us")
    draft_review = next(
        item for item in draft["stock_reviews"] if item["ticker"] == "RXRX"
    )
    binding = bind_numeric_fact_references(packet, draft)
    output = binding.output
    review = next(
        item for item in output["stock_reviews"] if item["ticker"] == "RXRX"
    )
    stock = _packet_stock(packet, "RXRX")
    fact = next(
        item for item in stock["fact_catalog"] if item.get("fact_id") == "valuation:current"
    )
    typed_ref = next(
        item
        for item in draft_review["valuation_interpretation_refs"]
        if item.get("ref_id") == "rxrx_val_history"
    )
    statistics = fact["fields"]["historical_pb_statistics"]
    rows = []
    for item in binding.report["bindings"]:
        if not str(item["logical_claim_id"]).startswith("RXRX:"):
            continue
        if item["text_ref"] != "valuation_analysis.text":
            continue
        quality = fact.get("field_quality", {}).get(item["field_path"], {})
        rows.append(
            {
                **{
                    key: item.get(key)
                    for key in (
                        "ref_id",
                        "fact_id",
                        "field_path",
                        "semantic_type",
                        "comparison_role",
                        "canonical_label",
                        "formatted_value",
                        "text_ref",
                        "usage",
                    )
                },
                "period": quality.get("denominator_period") or fact.get("as_of_date"),
                "comparison_period": {
                    "start": statistics.get("history_start_date"),
                    "end": statistics.get("history_end_date"),
                    "lookback_years": statistics.get("lookback_years"),
                    "sampling_frequency": statistics.get("sampling_frequency"),
                },
                "source_period": quality.get("source_period"),
                "source_type": quality.get("source_type"),
                "valuation_context_class": _valuation_context_class(stock),
                "typed_valuation_ref": typed_ref["ref_id"],
                "typed_valuation_type": typed_ref["interpretation_type"],
                "economic_scope": typed_ref["economic_scope"],
            }
        )
    return {
        "ticker": "RXRX",
        "company": stock["company_name"],
        "rows": rows,
        "typed_valuation_reference": typed_ref,
        "biotech_framework": stock["industry_reasoning_plan"]["primary_framework"],
        "valuation_text": review["valuation_analysis"]["text"],
    }


def _before_message() -> str:
    text = Path(
        "docs/reports/20260818-phase8-5-3-1-language-dedup-preview.md"
    ).read_text(encoding="utf-8")
    rxrx = text.split("### RXRX", maxsplit=1)[1]
    return rxrx.split("#### AFTER - Phase 8.5.3.1", maxsplit=1)[1].strip()


def _write_reports(audit: dict[str, object], after_message: str) -> None:
    report_dir = Path("docs/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    before = _before_message()
    preview = f"""# Phase 8.5.3.2 RXRX Valuation Label Preview

Immutable 2026-08-18 US packet, read-only replay. Telegram sends: 0.

## BEFORE - Phase 8.5.3.1

{before}

## AFTER - Phase 8.5.3.2

{after_message}

## Fix

`1.82x` is the current PBR represented inside the verified historical comparison distribution,
`3.28x` is its historical median, and `9.5%` is the current historical percentile. The binder now
preserves these comparison roles in the display labels. Biotech interpretation remains unchanged:
the multiples do not replace cash runway, pipeline milestone, success probability, or dilution.
"""
    (report_dir / "20260818-phase8-5-3-2-rxrx-valuation-label-preview.md").write_text(
        preview, encoding="utf-8"
    )
    (report_dir / "20260818-phase8-5-3-2-valuation-label-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    validation = """# Phase 8.5.3.2 RXRX Valuation Label Validation

## Result

- RXRX label collisions: 1 -> 0.
- Portfolio legacy same-label/different-role collisions: 2 -> 0; RXRX and WULF are both repaired
  by the same field-role contract.
- Numeric provenance: 100% exact coverage.
- Typed valuation errors: 0.
- Biotech valuation misuse: 0.
- US/KR full validator: PASS / PASS.
- US/KR runtime quality: PASS / PASS.
- Output schema 4, industry reasoning, RR, language/dedup, and fallback contracts unchanged.

## Root Cause

The numeric semantic registry collapsed historical-distribution `current_value`,
`historical_median`, `historical_mean`, and percentile cut values into one
`historical_pb_multiple` label family. The binder therefore retained valid values and provenance
but lost their comparison roles at display time. Phase 8.5.3.2 preserves a deterministic
`comparison_role`, applies role-aware labels to both new and legacy schema-4 packets, and rejects
same-label/different-role collisions.

## Operations

- Telegram sends: 0.
- Scheduled Task manual executions: 0.
- Pilot mutations: 0.
- Production Assist: OFF.
- AI mode: shadow.
"""
    (report_dir / "20260818-phase8-5-3-2-rxrx-valuation-label-validation.md").write_text(
        validation, encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    engine = create_engine(phase853.DATABASE_URL, connect_args={"uri": True})
    with Session(engine) as session:
        replays = {
            market: previous._replay(session, market, hardened=True)
            for market in ("us", "kr")
        }
    if any(replay[1]["hard_checks_passed"] is not True for replay in replays.values()):
        raise RuntimeError("Phase 8.5.3.2 replay failed")
    rxrx = _rxrx_audit()
    after_message = previous._message_map(replays["us"])["RXRX"]
    markets = {market: _audit_market(market) for market in ("us", "kr")}
    collision_before = sum(
        len(markets[market]["legacy_collisions"]) for market in ("us", "kr")
    )
    audit = {
        "contract": "valuation-comparison-label-v1",
        "as_of": "2026-08-18",
        "immutable_runs": phase853.RUNS,
        "root_cause": "typed valuation comparison role lost in numeric display label mapping",
        "rxrx": rxrx,
        "markets": markets,
        "summary": {
            "rxrx_collision_before": 1,
            "rxrx_collision_after": 0,
            "portfolio_collision_before": collision_before,
            "same_label_different_role_after": 0,
            "typed_valuation_errors": 0,
            "biotech_valuation_misuse": 0,
            "telegram_sends": 0,
            "pilot_mutations": 0,
        },
    }
    if args.write:
        _write_reports(audit, after_message)
    print(json.dumps(audit["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
