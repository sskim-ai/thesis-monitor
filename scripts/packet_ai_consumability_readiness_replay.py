from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from app.services.cross_market_decision_engine_service import (
    build_decision_evidence_packet,
)
from app.services.fact_consumer_scope_service import (
    MARKET_CONTEXT_CONSUMER_SCOPES,
    NIGHT_FUTURES_CONSUMER_SCOPES,
    FactConsumer,
    fact_consumer_scopes,
    with_added_fact_consumer_scope,
    with_fact_consumer_scopes,
)
from app.services.numeric_semantic_registry import (
    build_numeric_registry,
    consumer_numeric_registry_coverage,
)


CONTRACT = "packet-ai-consumability-readiness-replay-v1"


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _facts(value: object) -> list[dict[str, object]]:
    return [dict(row) for row in value or () if isinstance(row, Mapping)]


def _market_fact_with_scope(fact: Mapping[str, object]) -> dict[str, object]:
    existing = fact_consumer_scopes(fact)
    if existing is not None:
        return with_fact_consumer_scopes(
            fact,
            existing,
            user_visible=(
                fact.get("user_visible")
                if isinstance(fact.get("user_visible"), bool)
                else None
            ),
        )
    if str(fact.get("fact_type") or "") in {
        "night_futures",
        "night_futures_timeframe",
    }:
        return with_fact_consumer_scopes(
            fact,
            NIGHT_FUTURES_CONSUMER_SCOPES,
            user_visible=False,
        )
    return with_fact_consumer_scopes(fact, MARKET_CONTEXT_CONSUMER_SCOPES)


def _canonical_payload(facts: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            key: value
            for key, value in fact.items()
            if key not in {"consumer_scope_contract", "consumer_scopes", "user_visible"}
        }
        for fact in facts
    ]


def replay(packet_path: Path) -> tuple[dict[str, object], dict[str, object]]:
    source_sha_before = _sha256(packet_path)
    packet = _read_json(packet_path)
    market_context = packet.get("market_context")
    if not isinstance(market_context, dict):
        raise ValueError("market_context_missing")
    original_market_facts = _facts(market_context.get("fact_catalog"))
    original_stock_facts = {
        str(stock.get("ticker") or ""): _facts(stock.get("fact_catalog"))
        for stock in packet.get("stocks") or ()
        if isinstance(stock, Mapping)
    }
    original_fact_count = len(original_market_facts) + sum(
        len(rows) for rows in original_stock_facts.values()
    )

    market_facts = [_market_fact_with_scope(fact) for fact in original_market_facts]
    market_by_id = {
        str(fact.get("fact_id")): fact for fact in market_facts if fact.get("fact_id")
    }
    market_registry = build_numeric_registry(market_facts)
    market_context["fact_catalog"] = market_facts
    market_context["numeric_registry"] = market_registry

    surfaces: list[dict[str, object]] = [
        {"name": "market_context", "registry": market_registry}
    ]
    evidence_by_ticker: dict[str, set[str]] = {}
    stock_numeric_count = 0
    for stock_value in packet.get("stocks") or ():
        if not isinstance(stock_value, dict):
            continue
        ticker = str(stock_value.get("ticker") or "")
        stock_facts = []
        for fact in _facts(stock_value.get("fact_catalog")):
            fact_id = str(fact.get("fact_id") or "")
            market_fact = market_by_id.get(fact_id)
            if market_fact is None:
                stock_facts.append(fact)
                continue
            scopes = fact_consumer_scopes(market_fact) or ()
            scoped = with_fact_consumer_scopes(
                fact,
                scopes,
                user_visible=(
                    market_fact.get("user_visible")
                    if isinstance(market_fact.get("user_visible"), bool)
                    else None
                ),
            )
            stock_facts.append(
                with_added_fact_consumer_scope(scoped, FactConsumer.STOCK_V2)
            )
        stock_registry = build_numeric_registry(stock_facts)
        stock_value["fact_catalog"] = stock_facts
        stock_value["numeric_registry"] = stock_registry
        stock_numeric_count += len(stock_registry)
        surfaces.append({"name": f"stock:{ticker}", "registry": stock_registry})
        evidence = build_decision_evidence_packet(packet=packet, stock=stock_value)
        evidence_by_ticker[ticker] = {
            row.ref_id.removeprefix("canonical:")
            for row in evidence.evidence
            if row.ref_id.startswith("canonical:")
        }

    coverage = consumer_numeric_registry_coverage(
        surfaces,
        consumer=FactConsumer.STOCK_V2,
    )
    profile_gate = packet.get("shadow_cohort", {})
    profile_gate = (
        profile_gate.get("profile_gate") if isinstance(profile_gate, Mapping) else {}
    )
    ready = bool(
        isinstance(profile_gate, Mapping)
        and profile_gate.get("ready") is True
        and coverage.get("ready") is True
    )
    included_prompt_mismatches: list[str] = []
    for surface in surfaces[1:]:
        surface_name = str(surface["name"])
        ticker = surface_name.removeprefix("stock:")
        prompt_ids = evidence_by_ticker[ticker]
        for row in surface["registry"]:
            if not isinstance(row, Mapping):
                continue
            scopes = row.get("consumer_scopes")
            if isinstance(scopes, (list, tuple)) and FactConsumer.STOCK_V2.value not in {
                str(item) for item in scopes
            }:
                continue
            fact_id = str(row.get("fact_id") or "")
            if fact_id and fact_id not in prompt_ids:
                included_prompt_mismatches.append(
                    f"{surface_name}:{fact_id}:{row.get('field_path')}"
                )

    repaired_fact_count = len(market_facts) + sum(
        len(_facts(stock.get("fact_catalog")))
        for stock in packet.get("stocks") or ()
        if isinstance(stock, Mapping)
    )
    raw_payload_preserved = (
        _canonical_payload(original_market_facts) == _canonical_payload(market_facts)
        and all(
            _canonical_payload(original_stock_facts[ticker])
            == _canonical_payload(
                _facts(
                    next(
                        stock.get("fact_catalog")
                        for stock in packet.get("stocks") or ()
                        if isinstance(stock, Mapping)
                        and str(stock.get("ticker") or "") == ticker
                    )
                )
            )
            for ticker in original_stock_facts
        )
    )
    source_sha_after = _sha256(packet_path)
    reference_exclusions = [
        row
        for row in coverage["excluded_nonconsumer"]
        if row.get("fact_id")
        in {"market:night_futures:1", "market:night_futures:2"}
        and row.get("field_path") == "fields.reference_price"
    ]
    result = {
        "contract": CONTRACT,
        "packet_id": packet.get("packet_id"),
        "source": {
            "path": str(packet_path),
            "sha256_before": source_sha_before,
            "sha256_after": source_sha_after,
            "production_packet_mutated": int(source_sha_before != source_sha_after),
        },
        "before": {
            "ready_for_ai": packet.get("ready_for_ai"),
            "numeric_semantic_gate": (
                packet.get("shadow_cohort", {}).get("numeric_semantic_gate")
                if isinstance(packet.get("shadow_cohort"), Mapping)
                else None
            ),
            "canonical_fact_count": original_fact_count,
        },
        "after": {
            "consumer": FactConsumer.STOCK_V2.value,
            "ready_for_ai": ready,
            "numeric_semantic_gate": coverage,
            "canonical_fact_count": repaired_fact_count,
            "market_numeric_count": len(market_registry),
            "stock_numeric_count": stock_numeric_count,
            "subject_count": len(evidence_by_ticker),
            "reference_price_exclusions": reference_exclusions,
        },
        "prompt_parity": {
            "subject_count": len(evidence_by_ticker),
            "included_numeric_prompt_mismatch_count": len(included_prompt_mismatches),
            "included_numeric_prompt_mismatches": included_prompt_mismatches,
            "standalone_market_surface_sent_to_stock_v2": 0,
        },
        "preservation": {
            "fact_count_preserved": original_fact_count == repaired_fact_count,
            "raw_payload_preserved": raw_payload_preserved,
            "night_fact_count": sum(
                fact.get("fact_type") in {"night_futures", "night_futures_timeframe"}
                for fact in market_facts
            ),
            "night_facts_stock_v2_consumable": sum(
                FactConsumer.STOCK_V2 in (fact_consumer_scopes(fact) or ())
                for fact in market_facts
                if fact.get("fact_type") in {"night_futures", "night_futures_timeframe"}
            ),
            "night_facts_daily_review_consumable": sum(
                FactConsumer.DAILY_REVIEW in (fact_consumer_scopes(fact) or ())
                for fact in market_facts
                if fact.get("fact_type") in {"night_futures", "night_futures_timeframe"}
            ),
        },
        "gates": {
            "RUN53_STOCK_V2_READY_FOR_AI": ready,
            "RUN53_UNSUPPORTED_INCLUDED_STOCK_V2_NUMERICS": coverage[
                "unsupported_included_numeric_count"
            ],
            "RUN53_CANONICAL_RAW_FACT_COUNT_PRESERVED": (
                "PASS"
                if original_fact_count == repaired_fact_count and raw_payload_preserved
                else "FAIL"
            ),
            "READINESS_PROMPT_CONSUMER_SURFACE_MISMATCH": len(
                included_prompt_mismatches
            ),
            "PRODUCTION_PACKET_MUTATION": int(source_sha_before != source_sha_after),
        },
    }
    scope_contract = {
        "contract": "packet-fact-consumer-scope-v1",
        "consumers": [item.value for item in FactConsumer],
        "fail_safe_default": "LEGACY_UNCLASSIFIED_STRICT",
        "night_futures": {
            "consumer_scopes": [
                item.value for item in NIGHT_FUTURES_CONSUMER_SCOPES
            ],
            "user_visible": False,
            "exclusion_reason": "NOT_IN_CONSUMER_SCOPE",
        },
        "market_context": {
            "consumer_scopes": [item.value for item in MARKET_CONTEXT_CONSUMER_SCOPES]
        },
        "stock_v2": {
            "readiness_contract": "ai-numeric-semantic-consumer-surface-v1",
            "included_numeric_count": coverage["included_numeric_count"],
            "excluded_nonconsumer_numeric_count": coverage[
                "excluded_nonconsumer_numeric_count"
            ],
        },
    }
    return result, scope_contract


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--contract-output", type=Path, required=True)
    args = parser.parse_args()
    result, scope_contract = replay(args.packet)
    _write_json(args.output, result)
    _write_json(args.contract_output, scope_contract)
    print(json.dumps(result["gates"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
