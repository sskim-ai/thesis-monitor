from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any


PROVIDER_DIALECT_CONTRACT = "openai-structured-outputs-provider-dialect-v1"
PROVIDER_WIRE_PROJECTION_CONTRACT = "m12cs-r1-provider-wire-schema-projection-v1"

ALLOWED_SCHEMA_KEYWORDS = frozenset(
    {
        "$defs",
        "$ref",
        "additionalProperties",
        "anyOf",
        "const",
        "description",
        "enum",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "format",
        "items",
        "maxItems",
        "maxLength",
        "maximum",
        "minItems",
        "minLength",
        "minimum",
        "multipleOf",
        "pattern",
        "properties",
        "required",
        "title",
        "type",
    }
)

EXPLICITLY_UNSUPPORTED_SCHEMA_KEYWORDS = frozenset(
    {
        "allOf",
        "dependentRequired",
        "dependentSchemas",
        "else",
        "if",
        "not",
        "then",
        "uniqueItems",
    }
)

ALLOWED_TYPES = frozenset({"array", "boolean", "integer", "null", "number", "object", "string"})

MAX_OBJECT_PROPERTIES = 5_000
MAX_SCHEMA_NESTING_DEPTH = 10
MAX_SCHEMA_STRING_BUDGET = 120_000
MAX_ENUM_VALUES = 1_000
MAX_LARGE_ENUM_STRING_BUDGET = 15_000
LARGE_ENUM_VALUE_THRESHOLD = 250

SEMANTIC_UNIQUENESS_RULES = (
    {
        "logical_field": "pass-a.archetype_supporting_claim_refs",
        "rule_id": "PA_ARCHETYPE_REF_DUPLICATE",
        "classification": "UNIQUENESS_SEMANTICALLY_REQUIRED",
    },
    {
        "logical_field": "pass-a.tier_supporting_claim_refs",
        "rule_id": "PA_TIER_REF_DUPLICATE",
        "classification": "UNIQUENESS_SEMANTICALLY_REQUIRED",
    },
    {
        "logical_field": "pass-a.directional_data_quality_judgment.evidence_refs",
        "rule_id": "PA_QUALITY_EVIDENCE_REF_DUPLICATE",
        "classification": "UNIQUENESS_SEMANTICALLY_REQUIRED",
    },
    {
        "logical_field": "pass-b.decisive_supporting_claim_refs",
        "rule_id": "PB_SUPPORT_REF_DUPLICATE",
        "classification": "UNIQUENESS_SEMANTICALLY_REQUIRED",
    },
    {
        "logical_field": "pass-b.decisive_contradicting_claim_refs",
        "rule_id": "PB_CONTRADICTION_REF_DUPLICATE",
        "classification": "UNIQUENESS_SEMANTICALLY_REQUIRED",
    },
    {
        "logical_field": "pass-b.holder_decision.evidence_refs",
        "rule_id": "PB_HOLDER_EVIDENCE_REF_DUPLICATE",
        "classification": "UNIQUENESS_SEMANTICALLY_REQUIRED",
    },
    {
        "logical_field": "pass-b.new_buyer_decision.evidence_refs",
        "rule_id": "PB_NEW_BUYER_EVIDENCE_REF_DUPLICATE",
        "classification": "UNIQUENESS_SEMANTICALLY_REQUIRED",
    },
    {
        "logical_field": "pass-b.new_buyer_decision.re_evaluate_conditions",
        "rule_id": "PB_REEVALUATE_CONDITION_DUPLICATE",
        "classification": "UNIQUENESS_SEMANTICALLY_REQUIRED",
    },
)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _schema_path(parts: Sequence[str | int]) -> str:
    rendered = "$"
    for part in parts:
        if isinstance(part, int):
            rendered += f"[{part}]"
        else:
            rendered += f".{part}"
    return rendered


def _enum_item_schema_key(node: object) -> str | None:
    if not isinstance(node, Mapping):
        return None
    if node.get("type") != "string" or not isinstance(node.get("enum"), list):
        return None
    if set(node) != {"type", "enum"}:
        return None
    return _canonical_json(node)


def _repeated_array_item_enums(schema: Mapping[str, object]) -> dict[str, str]:
    counts: Counter[str] = Counter()

    def visit(node: object) -> None:
        if isinstance(node, Mapping):
            key = _enum_item_schema_key(node.get("items"))
            if key is not None:
                counts[key] += 1
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(schema)
    repeated = sorted(key for key, count in counts.items() if count > 1)
    return {
        key: f"shared_string_enum_{hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]}"
        for key in repeated
    }


def project_provider_wire_schema(
    internal_schema: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    """Project the richer local contract into the provider-supported wire dialect."""

    shared_enums = _repeated_array_item_enums(internal_schema)
    removed_paths: list[str] = []
    shared_ref_paths: list[str] = []

    def transform(node: object, path: tuple[str | int, ...]) -> object:
        if isinstance(node, Mapping):
            projected: dict[str, object] = {}
            for key, child in node.items():
                if key == "uniqueItems":
                    removed_paths.append(_schema_path((*path, key)))
                    continue
                if key == "items":
                    enum_key = _enum_item_schema_key(child)
                    if enum_key in shared_enums:
                        name = shared_enums[enum_key]
                        projected[key] = {"$ref": f"#/$defs/{name}"}
                        shared_ref_paths.append(_schema_path((*path, key)))
                        continue
                projected[key] = transform(child, (*path, key))
            return projected
        if isinstance(node, list):
            return [transform(child, (*path, index)) for index, child in enumerate(node)]
        return deepcopy(node)

    wire = transform(internal_schema, ())
    if not isinstance(wire, dict):
        raise TypeError("provider_wire_schema_object_required")
    if shared_enums:
        existing_defs = wire.get("$defs")
        if existing_defs is not None and not isinstance(existing_defs, Mapping):
            raise TypeError("provider_wire_defs_mapping_required")
        definitions = dict(existing_defs or {})
        for encoded, name in sorted(shared_enums.items(), key=lambda item: item[1]):
            if name in definitions:
                raise ValueError(f"provider_wire_definition_collision:{name}")
            definitions[name] = json.loads(encoded)
        wire["$defs"] = definitions

    receipt = {
        "contract": PROVIDER_WIRE_PROJECTION_CONTRACT,
        "internal_semantic_schema_sha256": canonical_sha256(internal_schema),
        "provider_wire_schema_sha256": canonical_sha256(wire),
        "removed_keyword": "uniqueItems",
        "removed_keyword_count": len(removed_paths),
        "removed_keyword_paths": removed_paths,
        "shared_enum_definition_count": len(shared_enums),
        "shared_enum_reference_count": len(shared_ref_paths),
        "shared_enum_reference_paths": shared_ref_paths,
        "semantic_constraint_owner": "LOCAL_RAW_AND_SEMANTIC_VALIDATORS",
        "status": "PASS",
    }
    return wire, receipt


def _schema_keyword_inventory(
    schema: Mapping[str, object],
) -> tuple[Counter[str], list[dict[str, str]]]:
    counts: Counter[str] = Counter()
    rows: list[dict[str, str]] = []

    def visit(node: object, path: tuple[str | int, ...]) -> None:
        if not isinstance(node, Mapping):
            return
        for key in node:
            counts[key] += 1
            rows.append({"keyword": key, "path": _schema_path((*path, key))})
        properties = node.get("properties")
        if isinstance(properties, Mapping):
            for name, child in properties.items():
                visit(child, (*path, "properties", str(name)))
        definitions = node.get("$defs")
        if isinstance(definitions, Mapping):
            for name, child in definitions.items():
                visit(child, (*path, "$defs", str(name)))
        items = node.get("items")
        if isinstance(items, Mapping):
            visit(items, (*path, "items"))
        branches = node.get("anyOf")
        if isinstance(branches, list):
            for index, child in enumerate(branches):
                visit(child, (*path, "anyOf", index))

    visit(schema, ())
    return counts, rows


def provider_schema_keyword_inventory(schema: Mapping[str, object]) -> dict[str, object]:
    counts, rows = _schema_keyword_inventory(schema)
    return {
        "contract": "m12cs-r1-provider-schema-keyword-inventory-v1",
        "keyword_counts": dict(sorted(counts.items())),
        "keyword_occurrence_count": sum(counts.values()),
        "rows": rows,
    }


def provider_structured_output_dialect_contract() -> dict[str, object]:
    return {
        "contract": PROVIDER_DIALECT_CONTRACT,
        "official_reference": "https://developers.openai.com/api/docs/guides/structured-outputs",
        "allowed_schema_keywords": sorted(ALLOWED_SCHEMA_KEYWORDS),
        "explicitly_unsupported_schema_keywords": sorted(EXPLICITLY_UNSUPPORTED_SCHEMA_KEYWORDS),
        "allowed_types": sorted(ALLOWED_TYPES),
        "limits": {
            "object_properties": MAX_OBJECT_PROPERTIES,
            "schema_nesting_depth": MAX_SCHEMA_NESTING_DEPTH,
            "schema_string_budget": MAX_SCHEMA_STRING_BUDGET,
            "enum_values": MAX_ENUM_VALUES,
            "large_enum_threshold": LARGE_ENUM_VALUE_THRESHOLD,
            "large_enum_string_budget": MAX_LARGE_ENUM_STRING_BUDGET,
        },
        "empirical_provider_rejection": {
            "keyword": "uniqueItems",
            "error_code": "invalid_json_schema",
            "http_status": 400,
        },
        "projection_policy": {
            "uniqueItems": "REMOVE_FROM_WIRE_ENFORCE_LOCALLY",
            "repeated_reference_enums": "SHARE_WITH_DETERMINISTIC_DEFS_REFS",
            "other_unsupported_keywords": "FAIL_CLOSED",
        },
        "status": "PASS",
    }


def scan_provider_structured_output_schema(schema: Mapping[str, object]) -> dict[str, object]:
    counts, keyword_rows = _schema_keyword_inventory(schema)
    unsupported_rows = [
        row for row in keyword_rows if row["keyword"] not in ALLOWED_SCHEMA_KEYWORDS
    ]
    errors = [f"unsupported_keyword:{row['keyword']}:{row['path']}" for row in unsupported_rows]
    object_property_count = 0
    enum_value_count = 0
    schema_string_budget = 0
    max_nesting_depth = 0
    object_errors: list[dict[str, Any]] = []
    array_errors: list[dict[str, str]] = []
    type_errors: list[dict[str, object]] = []
    enum_errors: list[dict[str, object]] = []

    def visit(node: object, path: tuple[str | int, ...], nesting_depth: int) -> None:
        nonlocal object_property_count, enum_value_count, schema_string_budget
        nonlocal max_nesting_depth
        if not isinstance(node, Mapping):
            return
        node_type = node.get("type")
        types = node_type if isinstance(node_type, list) else [node_type]
        if node_type is not None and (
            not all(isinstance(item, str) and item in ALLOWED_TYPES for item in types)
        ):
            type_errors.append({"path": _schema_path(path), "type": node_type})
        is_container = "object" in types or "array" in types
        next_depth = nesting_depth + (1 if is_container else 0)
        max_nesting_depth = max(max_nesting_depth, next_depth)

        properties = node.get("properties")
        if isinstance(properties, Mapping):
            names = list(properties)
            object_property_count += len(names)
            schema_string_budget += sum(len(str(name)) for name in names)
            row_errors: list[str] = []
            if node.get("type") != "object":
                row_errors.append("properties_without_object_type")
            if node.get("additionalProperties") is not False:
                row_errors.append("additional_properties_not_false")
            required = node.get("required")
            if (
                not isinstance(required, list)
                or len(required) != len(names)
                or set(required) != set(names)
            ):
                row_errors.append("required_properties_mismatch")
            if row_errors:
                object_errors.append({"path": _schema_path(path), "errors": row_errors})
            for name, child in properties.items():
                visit(child, (*path, "properties", str(name)), next_depth)

        definitions = node.get("$defs")
        if isinstance(definitions, Mapping):
            schema_string_budget += sum(len(str(name)) for name in definitions)
            for name, child in definitions.items():
                visit(child, (*path, "$defs", str(name)), nesting_depth)

        if node.get("type") == "array":
            items = node.get("items")
            if not isinstance(items, Mapping):
                array_errors.append({"path": _schema_path(path), "error": "array_items_missing"})
            else:
                visit(items, (*path, "items"), next_depth)

        enum_values = node.get("enum")
        if isinstance(enum_values, list):
            enum_value_count += len(enum_values)
            enum_string_budget = sum(len(str(value)) for value in enum_values)
            schema_string_budget += enum_string_budget
            if (
                len(enum_values) > LARGE_ENUM_VALUE_THRESHOLD
                and enum_string_budget > MAX_LARGE_ENUM_STRING_BUDGET
            ):
                enum_errors.append(
                    {
                        "path": _schema_path(path),
                        "value_count": len(enum_values),
                        "string_budget": enum_string_budget,
                    }
                )
        if "const" in node:
            schema_string_budget += len(str(node["const"]))
        branches = node.get("anyOf")
        if isinstance(branches, list):
            for index, child in enumerate(branches):
                visit(child, (*path, "anyOf", index), nesting_depth)

    visit(schema, (), 0)
    if schema.get("type") != "object" or "anyOf" in schema:
        errors.append("root_must_be_object_without_anyof")
    errors.extend(
        f"strict_object:{row['path']}:{item}" for row in object_errors for item in row["errors"]
    )
    errors.extend(f"array:{row['path']}:{row['error']}" for row in array_errors)
    errors.extend(f"unsupported_type:{row['path']}:{row['type']}" for row in type_errors)
    errors.extend(f"large_enum_budget:{row['path']}" for row in enum_errors)
    if object_property_count > MAX_OBJECT_PROPERTIES:
        errors.append(f"object_property_limit:{object_property_count}")
    if max_nesting_depth > MAX_SCHEMA_NESTING_DEPTH:
        errors.append(f"schema_nesting_limit:{max_nesting_depth}")
    if schema_string_budget > MAX_SCHEMA_STRING_BUDGET:
        errors.append(f"schema_string_budget:{schema_string_budget}")
    if enum_value_count > MAX_ENUM_VALUES:
        errors.append(f"enum_value_limit:{enum_value_count}")

    return {
        "contract": PROVIDER_DIALECT_CONTRACT,
        "schema_sha256": canonical_sha256(schema),
        "keyword_counts": dict(sorted(counts.items())),
        "unsupported_keywords": unsupported_rows,
        "unsupported_keyword_count": len(unsupported_rows),
        "explicitly_rejected_keyword_count": sum(
            row["keyword"] in EXPLICITLY_UNSUPPORTED_SCHEMA_KEYWORDS for row in unsupported_rows
        ),
        "unique_items_count": counts.get("uniqueItems", 0),
        "object_property_count": object_property_count,
        "max_nesting_depth": max_nesting_depth,
        "schema_string_budget": schema_string_budget,
        "enum_value_count": enum_value_count,
        "object_errors": object_errors,
        "array_errors": array_errors,
        "type_errors": type_errors,
        "enum_errors": enum_errors,
        "errors": sorted(set(errors)),
        "error_count": len(set(errors)),
        "status": "PASS" if not errors else "FAIL",
    }


def logical_unique_items_inventory(
    schema: Mapping[str, object],
    *,
    stage: str,
    subjects: Sequence[str],
) -> list[dict[str, object]]:
    subject_set = set(subjects)
    rows: list[dict[str, object]] = []

    def visit(
        node: object,
        path: tuple[str | int, ...],
        logical_fields: tuple[str, ...],
    ) -> None:
        if not isinstance(node, Mapping):
            return
        if "uniqueItems" in node:
            logical = f"{stage}." + ".".join(logical_fields)
            rows.append(
                {
                    "path": _schema_path((*path, "uniqueItems")),
                    "logical_field": logical,
                    "value": node["uniqueItems"],
                }
            )
        properties = node.get("properties")
        if isinstance(properties, Mapping):
            for name, child in properties.items():
                field = str(name)
                next_fields = logical_fields
                if field not in {"classifications", "decisions"} and field not in subject_set:
                    next_fields = (*logical_fields, field)
                visit(child, (*path, "properties", field), next_fields)
        definitions = node.get("$defs")
        if isinstance(definitions, Mapping):
            for name, child in definitions.items():
                visit(child, (*path, "$defs", str(name)), logical_fields)
        items = node.get("items")
        if isinstance(items, Mapping):
            visit(items, (*path, "items"), logical_fields)
        branches = node.get("anyOf")
        if isinstance(branches, list):
            for index, child in enumerate(branches):
                visit(child, (*path, "anyOf", index), logical_fields)

    visit(schema, (), ())
    return rows


def semantic_uniqueness_rule(logical_field: str) -> Mapping[str, str] | None:
    return next(
        (row for row in SEMANTIC_UNIQUENESS_RULES if row["logical_field"] == logical_field),
        None,
    )
