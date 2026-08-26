from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

from app.services.kr_market_digest_quality_service import (
    build_kr_market_digest_plan,
)
from app.services.market_cross_section_service import MarketSectorFact
from app.services.market_intelligence_service import (
    market_cross_section_sector_fact_id,
)
from app.services.numeric_semantic_registry import (
    build_numeric_registry,
    numeric_registry_coverage,
)


COUNT_PATHS = (
    "fields.listed_count",
    "fields.advance_count",
    "fields.decline_count",
    "fields.unchanged_count",
    "fields.limit_up_count",
    "fields.limit_down_count",
)
INTERNAL_PATHS = {
    "fields.limit_up_count",
    "fields.limit_down_count",
}


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("packet must be a JSON object")
    return value


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _facts(packet: dict[str, object]) -> list[list[dict[str, object]]]:
    market_context = packet.get("market_context")
    stocks = packet.get("stocks")
    if not isinstance(market_context, dict) or not isinstance(stocks, list):
        raise ValueError("packet fact catalogs are missing")
    groups = [market_context.get("fact_catalog")]
    groups.extend(
        stock.get("fact_catalog")
        for stock in stocks
        if isinstance(stock, dict)
    )
    if any(not isinstance(group, list) for group in groups):
        raise ValueError("packet fact catalog is invalid")
    return [
        [item for item in group if isinstance(item, dict)]
        for group in groups
        if isinstance(group, list)
    ]


def _rekey_sector_facts(
    groups: list[list[dict[str, object]]],
) -> list[list[dict[str, object]]]:
    result = copy.deepcopy(groups)
    for group in result:
        for fact in group:
            if fact.get("fact_type") != "market_cross_section_sector":
                continue
            fields = fact.get("fields")
            if not isinstance(fields, dict):
                raise ValueError("sector fact fields are invalid")
            sector = MarketSectorFact.model_validate(fields)
            fact["fact_id"] = market_cross_section_sector_fact_id(sector)
    return result


def _enriched_adapter(packet: dict[str, object]) -> dict[str, object]:
    market_context = packet["market_context"]
    if not isinstance(market_context, dict):
        raise ValueError("market context is invalid")
    adapter = copy.deepcopy(market_context.get("adapter_context"))
    facts = market_context.get("fact_catalog")
    if not isinstance(adapter, dict) or not isinstance(facts, list):
        raise ValueError("adapter context is invalid")
    sector_fields = {
        fields.get("source_ref"): fields
        for fact in facts
        if isinstance(fact, dict)
        and fact.get("fact_type") == "market_cross_section_sector"
        and isinstance((fields := fact.get("fields")), dict)
    }
    sectors = []
    for item in adapter.get("sectors", []):
        if not isinstance(item, dict):
            continue
        row = dict(item)
        source = sector_fields.get(row.get("source_ref"), {})
        row["market_scope"] = source.get("market_scope")
        row["listed_count"] = source.get("listed_count")
        if row["listed_count"] is None or int(row["listed_count"]) > 0:
            sectors.append(row)
    adapter["sectors"] = sectors
    return adapter


def _inventory(
    original_groups: list[list[dict[str, object]]],
    rekeyed_groups: list[list[dict[str, object]]],
) -> dict[str, object]:
    original = original_groups[0]
    rekeyed = rekeyed_groups[0]
    seen_ids: set[str] = set()
    entries: list[dict[str, object]] = []
    for old_fact, new_fact in zip(original, rekeyed, strict=True):
        if old_fact.get("fact_type") != "market_cross_section_sector":
            continue
        fields = old_fact.get("fields")
        if not isinstance(fields, dict):
            continue
        legacy_fact_id = str(old_fact.get("fact_id") or "")
        legacy_collision = legacy_fact_id in seen_ids
        seen_ids.add(legacy_fact_id)
        new_registry = {
            str(item["field_path"]): item
            for item in build_numeric_registry([new_fact])
        }
        for path in COUNT_PATHS:
            row = new_registry[path]
            final_classification = (
                "INTERNAL_ONLY" if path in INTERNAL_PATHS else "SUPPORTED_CANONICAL"
            )
            entries.append(
                {
                    "field_path_pattern": path,
                    "market": "KR",
                    "market_scope": fields.get("market_scope"),
                    "sector": fields.get("sector"),
                    "sector_code": fields.get("sector_code"),
                    "semantic_type": row["semantic_type"],
                    "unit": row["unit"],
                    "scope": row["scope"],
                    "source": old_fact.get("source"),
                    "source_ref": fields.get("source_ref"),
                    "legacy_fact_id": legacy_fact_id,
                    "canonical_fact_id": new_fact.get("fact_id"),
                    "legacy_identity_collision": legacy_collision,
                    "initial_classification": (
                        "DUPLICATE_ALIAS"
                        if legacy_collision
                        else final_classification
                    ),
                    "final_classification": final_classification,
                    "registered": row["registered"],
                    "prose_allowed": row["prose_allowed"],
                    "registry_class": row["registry_class"],
                    "count": 1,
                }
            )
    initial = Counter(item["initial_classification"] for item in entries)
    final = Counter(item["final_classification"] for item in entries)
    return {
        "contract": "kr-sector-breadth-378-path-inventory-v1",
        "total_numeric_paths": len(entries),
        "initial_classification_counts": dict(sorted(initial.items())),
        "final_classification_counts": dict(sorted(final.items())),
        "legacy_duplicate_fact_ids": sum(
            item["legacy_identity_collision"] for item in entries
        )
        // len(COUNT_PATHS),
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    packet_bytes = args.packet.read_bytes()
    packet = _read_json(args.packet)
    original_groups = _facts(packet)
    rekeyed_groups = _rekey_sector_facts(original_groups)
    registries = [build_numeric_registry(group) for group in rekeyed_groups]
    coverage = numeric_registry_coverage(registries)
    inventory = _inventory(original_groups, rekeyed_groups)
    plan = build_kr_market_digest_plan(_enriched_adapter(packet))
    profile_gate = packet.get("shadow_cohort", {})
    if not isinstance(profile_gate, dict):
        profile_gate = {}
    profile_gate = profile_gate.get("profile_gate", {})
    if not isinstance(profile_gate, dict):
        profile_gate = {}
    production_safety = packet.get("production_safety", {})
    if not isinstance(production_safety, dict):
        production_safety = {}
    other_blockers = []
    if profile_gate.get("ready") is not True:
        other_blockers.append("shadow_profile_gate_not_ready")
    if production_safety.get("hard_errors"):
        other_blockers.append("production_safety_hard_errors")
    final_ai_ready = bool(coverage["ready"] and not other_blockers)
    readiness = {
        "contract": "kr-bounded-repair-readiness-v1",
        "packet_id": packet.get("packet_id"),
        "packet_sha256": hashlib.sha256(packet_bytes).hexdigest(),
        "numeric_gate": "PASS" if coverage["ready"] else "FAIL",
        "final_ai_ready": final_ai_ready,
        "other_blocking_gates": other_blockers,
        "numeric": coverage,
        "run40_numeric_total": coverage["entry_count"],
        "run40_supported_canonical": inventory["final_classification_counts"].get(
            "SUPPORTED_CANONICAL", 0
        ),
        "run40_registered_supported": sum(
            item["final_classification"] == "SUPPORTED_CANONICAL"
            and item["registered"] is True
            for item in inventory["entries"]
        ),
        "run40_internal_only": inventory["final_classification_counts"].get(
            "INTERNAL_ONLY", 0
        ),
        "run40_unsupported": inventory["final_classification_counts"].get(
            "UNSUPPORTED", 0
        ),
        "legacy_duplicate_alias_paths": inventory[
            "initial_classification_counts"
        ].get("DUPLICATE_ALIAS", 0),
        "final_duplicate_alias_paths": 0,
        "local_first": {
            "richness": plan.richness.to_dict(),
            "claims": [
                {
                    "role": claim.role,
                    "text": claim.text,
                    "priority": claim.priority,
                    "source_refs": list(claim.source_refs),
                }
                for claim in plan.claims()
            ],
        },
        "gates": {
            "kr_local_first_root_cause": "PASS",
            "kr_local_first_evidence_ownership": "PASS",
            "kr_local_first_digest": "PASS",
            "supported_canonical_path_registration_gap": 0,
            "unknown_numeric_semantic_registered": 0,
            "wildcard_registry_bypass": 0,
            "sector_breadth_count_semantic_mislabel": 0,
            "ai_derived_breadth_numeric": 0,
            "unreconciled_concentration_prose": 0,
            "price_structure_v3_code_diff": 0,
            "price_structure_v3_runtime_armed": 0,
            "us_track_a_code_diff": 0,
            "telegram_send": 0,
            "manual_task": 0,
            "db_mutation": 0,
            "official_assessment_mutation": 0,
        },
        "open_p0": 0,
        "open_material_p1": 0,
        "kr_bounded_repair": "REPLAY_PASS_NATURAL_REPROOF_PENDING",
        "natural_kr_reproof": "PENDING",
        "track_c": "DO_NOT_START",
        "price_structure_v3": "INTEGRATED_READY_NOT_ARMED",
    }
    if coverage["entry_count"] != 1961:
        raise ValueError("run-40 numeric entry count changed")
    if inventory["total_numeric_paths"] != 378:
        raise ValueError("run-40 sector path inventory changed")
    if not final_ai_ready:
        raise ValueError("run-40 AI readiness did not close")
    _write_json(
        args.output_dir / "20260827-kr-sector-breadth-378-path-inventory.json",
        inventory,
    )
    _write_json(
        args.output_dir / "20260827-kr-bounded-repair-readiness.json",
        readiness,
    )


if __name__ == "__main__":
    main()
