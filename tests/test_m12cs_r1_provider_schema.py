from __future__ import annotations

import json
from pathlib import Path

from scripts.m12cr_shadow_contract import future_pass_a_batch_schema
from scripts.m12cs_fresh_two_pass_shadow import _classify_m12cs_failure
from scripts.m12cs_r1_provider_schema import (
    logical_unique_items_inventory,
    project_provider_wire_schema,
    provider_schema_keyword_inventory,
    scan_provider_structured_output_schema,
)


def _strict_object(properties: dict[str, object]) -> dict[str, object]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _context() -> dict[str, object]:
    return {
        "eligible_claim_refs": ["claim:one", "claim:two"],
        "premium_eligible_claim_refs": ["claim:one"],
        "data_quality_catalog": {
            "material_disclosure_failure_refs": ["quality:negative"],
            "positive_quality_refs": ["quality:positive"],
        },
    }


def test_provider_projection_is_deterministic_and_semantics_preserving() -> None:
    shared_items = {"type": "string", "enum": ["ref:one", "ref:two"]}
    internal = _strict_object(
        {
            "left": {
                "type": "array",
                "items": shared_items,
                "minItems": 1,
                "maxItems": 2,
                "uniqueItems": True,
            },
            "right": {
                "type": "array",
                "items": shared_items,
                "minItems": 0,
                "maxItems": 2,
                "uniqueItems": True,
            },
        }
    )

    first, first_receipt = project_provider_wire_schema(internal)
    second, second_receipt = project_provider_wire_schema(internal)

    assert first == second
    assert first_receipt == second_receipt
    assert first_receipt["removed_keyword_count"] == 2
    assert first_receipt["shared_enum_definition_count"] == 1
    assert first_receipt["shared_enum_reference_count"] == 2
    assert first["properties"]["left"]["items"]["$ref"].startswith("#/$defs/")
    assert scan_provider_structured_output_schema(first)["status"] == "PASS"
    assert provider_schema_keyword_inventory(first)["keyword_counts"].get("uniqueItems", 0) == 0


def test_provider_dialect_rejects_all_unsupported_keywords_with_paths() -> None:
    schema = _strict_object(
        {
            "refs": {
                "type": "array",
                "items": {"type": "string"},
                "uniqueItems": True,
                "not": {"type": "null"},
            }
        }
    )

    result = scan_provider_structured_output_schema(schema)

    assert result["status"] == "FAIL"
    assert result["unique_items_count"] == 1
    assert {row["keyword"] for row in result["unsupported_keywords"]} == {
        "not",
        "uniqueItems",
    }
    assert all(row["path"].startswith("$.") for row in result["unsupported_keywords"])


def test_logical_inventory_collapses_expanded_pass_a_branches() -> None:
    schema = future_pass_a_batch_schema(
        subjects=("AAA",),
        subject_contexts={"AAA": _context()},
    )

    rows = logical_unique_items_inventory(schema, stage="pass-a", subjects=("AAA",))

    assert len(rows) > 3
    assert {row["logical_field"] for row in rows} == {
        "pass-a.archetype_supporting_claim_refs",
        "pass-a.directional_data_quality_judgment.evidence_refs",
        "pass-a.tier_supporting_claim_refs",
    }


def test_m12cs_provider_schema_rejection_gets_precise_causal_category(tmp_path: Path) -> None:
    log = tmp_path / "transport.log"
    log.write_text(
        "ERROR:"
        + json.dumps(
            {
                "error": {
                    "type": "invalid_request_error",
                    "code": "invalid_json_schema",
                    "message": "uniqueItems is not permitted",
                },
                "status": 400,
            }
        ),
        encoding="utf-8",
    )

    category = _classify_m12cs_failure(
        RuntimeError("OTHER_TRANSPORT_FAILURE:attempts=1"),
        log,
        execution_stage="TRANSPORT",
    )

    assert category == "PROVIDER_SCHEMA_DIALECT_REJECTED_PRE_INFERENCE"
