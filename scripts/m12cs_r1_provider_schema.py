from __future__ import annotations

import hashlib
import json
import math
import re
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

# These paths are owned ref arrays in the B2 contract, not a suffix-based heuristic.
EMPTY_REF_ARRAY_PATHS = frozenset({
    ("new_buyer_shadow", "valuation_context", name)
    for name in ("valuation_evidence_refs", "business_evidence_refs", "relation_refs")
} | {
    ("new_buyer_shadow", "reason_evidence_refs"),
    ("new_buyer_shadow", "active_risk_refs"),
    ("new_buyer_shadow", "timing_context", "evidence_refs"),
})


def infer_const_json_type(value: object, active: frozenset[int] = frozenset()) -> str:
    """Accept only finite JSON-native values; bool must precede integer."""
    if value is None:
        return "null"
    primitive = {str: "string", bool: "boolean", int: "integer", float: "number"}
    if type(value) in primitive:
        if type(value) is float and not math.isfinite(value):
            raise ValueError("provider_const_nonfinite_number")
        return primitive[type(value)]
    if type(value) not in (dict, list) or id(value) in active:
        raise ValueError("provider_const_unsupported_value")
    active = active | {id(value)}
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise ValueError("provider_const_unsupported_object_key")
        children = value.values()
    else:
        children = value
    for child in children:
        infer_const_json_type(child, active)
    return "object" if isinstance(value, dict) else "array"


def _const_type_matches(value_type: str, declared: object) -> bool:
    types = declared if isinstance(declared, list) else [declared]
    return bool(types) and all(isinstance(t, str) and t in ALLOWED_TYPES for t in types) and (
        value_type in types or value_type == "integer" and "number" in types
    )


def _const_constraints(node: Mapping[str, object], kind: str) -> None:
    value = node["const"]
    allowed = {"const", "type", "title", "description"}
    allowed |= ({"enum", "minLength", "maxLength", "pattern"} if kind == "string" else
                {"enum", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"}
                if kind in {"integer", "number"} else {"enum"} if kind in {"boolean", "null"}
                else {"items", "minItems", "maxItems"} if kind == "array" else set())
    if set(node) - allowed:
        raise ValueError("provider_const_constraint_review_required")
    if "enum" in node:
        values = node["enum"]
        if not isinstance(values, list) or not any(
            infer_const_json_type(v) == kind and v == value for v in values
        ):
            raise ValueError("provider_const_constraint_mismatch")
    checks = {
        "minLength": lambda bound: type(bound) is int and bound >= 0 and len(value) >= bound,
        "maxLength": lambda bound: type(bound) is int and bound >= 0 and len(value) <= bound,
        "minItems": lambda bound: type(bound) is int and bound >= 0 and len(value) >= bound,
        "maxItems": lambda bound: type(bound) is int and bound >= 0 and len(value) <= bound,
        "minimum": lambda bound: value >= bound,
        "maximum": lambda bound: value <= bound,
        "exclusiveMinimum": lambda bound: value > bound,
        "exclusiveMaximum": lambda bound: value < bound,
        "multipleOf": lambda bound: bound > 0 and value % bound == 0,
        "pattern": lambda pattern: isinstance(pattern, str) and re.search(pattern, value) is not None,
    }
    try:
        for key, check in checks.items():
            if key in node:
                bound = node[key]
                if key in {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"}:
                    if infer_const_json_type(bound) not in {"integer", "number"}:
                        raise ValueError("provider_const_constraint_mismatch")
                if not check(bound):
                    raise ValueError("provider_const_constraint_mismatch")
    except (TypeError, re.error) as exc:
        raise ValueError("provider_const_constraint_mismatch") from exc


def _lower_const_schema(
    node: Mapping[str, object], path: tuple[str | int, ...], logical: tuple[str, ...],
    lowered: dict[str, list[str]],
) -> dict[str, object]:
    if "const" in node:
        kind = infer_const_json_type(node["const"])
        if "type" in node and not _const_type_matches(kind, node["type"]):
            raise ValueError("provider_const_type_mismatch")
        _const_constraints(node, kind)
        value = node["const"]
        if kind == "object":
            lowered["object"].append(_schema_path(path))
            props = {key: _lower_const_schema({"const": child}, (*path, "properties", key),
                     (*logical, key), lowered) for key, child in value.items()}
            result = dict(type="object", properties=props, required=list(props), additionalProperties=False)
        elif kind == "array":
            lowered["array"].append(_schema_path(path))
            types = {infer_const_json_type(child) for child in value}
            if not value:
                item = node.get("items")
                if (isinstance(item, Mapping) and set(item) == {"type"}
                        and isinstance(item["type"], str) and item["type"] in {
                    "string", "boolean", "integer", "number", "null"
                }):
                    item_type = item["type"]
                elif item is not None:
                    raise ValueError("provider_const_constraint_review_required")
                elif logical in EMPTY_REF_ARRAY_PATHS:
                    item_type = "string"
                    lowered["empty_ref_array"].append(_schema_path(path))
                else:
                    raise ValueError("provider_empty_const_array_item_type_unowned")
                items = {"type": item_type}
            else:
                if len(types) == 1 and not types & {"array", "object"}:
                    item_type = next(iter(types))
                elif types <= {"integer", "number"}:
                    item_type = "number"
                else:
                    raise ValueError("provider_complex_const_array_review_required")
                explicit = node.get("items")
                if explicit is not None and explicit != {"type": item_type}:
                    raise ValueError("provider_const_constraint_review_required")
                finite_values = list(dict.fromkeys(value))
                items = {"type": item_type, "enum": finite_values}
            if node.get("items") is not None and not isinstance(node["items"], Mapping):
                raise ValueError("provider_const_constraint_review_required")
            result = dict(type="array", items=items, minItems=len(value), maxItems=len(value))
        else:
            lowered["primitive"].append(_schema_path(path))
            return {**deepcopy(node), "type": deepcopy(node.get("type", kind))}
        for key in ("title", "description"):
            if key in node:
                result[key] = deepcopy(node[key])
        return result
    # Only schema-bearing fields are traversed. Literal const/enum payloads are data.
    result = deepcopy(dict(node))
    for keyword in ("properties", "$defs"):
        if isinstance(node.get(keyword), Mapping):
            result[keyword] = {key: _lower_const_schema(child, (*path, keyword, key),
                (*logical, key) if keyword == "properties" else (), lowered)
                if isinstance(child, Mapping) else deepcopy(child)
                for key, child in node[keyword].items()}
    if isinstance(node.get("items"), Mapping):
        result["items"] = _lower_const_schema(node["items"], (*path, "items"), (*logical, "[]"), lowered)
    if isinstance(node.get("anyOf"), list):
        result["anyOf"] = [_lower_const_schema(child, (*path, "anyOf", i), logical, lowered)
            if isinstance(child, Mapping) else deepcopy(child) for i, child in enumerate(node["anyOf"])]
    return result

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
            for keyword in ("properties", "$defs"):
                values = node.get(keyword)
                if isinstance(values, Mapping):
                    for child in values.values():
                        visit(child)
            visit(node.get("items"))
            for child in node.get("anyOf", []):
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

    lowered_paths: dict[str, list[str]] = {
        "primitive": [], "object": [], "array": [], "empty_ref_array": [],
    }
    typed_schema = _lower_const_schema(internal_schema, (), (), lowered_paths)
    shared_enums = _repeated_array_item_enums(typed_schema)
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
                if key in {"properties", "$defs"} and isinstance(child, Mapping):
                    projected[key] = {name: transform(value, (*path, key, name))
                                      for name, value in child.items()}
                elif key == "items" and isinstance(child, Mapping):
                    projected[key] = transform(child, (*path, key))
                elif key == "anyOf" and isinstance(child, list):
                    projected[key] = [transform(value, (*path, key, i))
                                      for i, value in enumerate(child)]
                else:
                    projected[key] = deepcopy(child)
            return projected
        return deepcopy(node)

    wire = transform(typed_schema, ())
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
        "const_lowering": {
            "contract": "provider-wire-typed-const-v1",
            "paths": lowered_paths,
            "counts": {key: len(paths) for key, paths in lowered_paths.items()},
            "array_exact_equality_owner": "UNCHANGED_LOCAL_SEMANTIC_SCHEMA",
        },
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
    const_errors: list[dict[str, str]] = []
    shape_errors: list[str] = []

    def visit(node: object, path: tuple[str | int, ...], nesting_depth: int) -> None:
        nonlocal object_property_count, enum_value_count, schema_string_budget
        nonlocal max_nesting_depth
        if not isinstance(node, Mapping):
            shape_errors.append(f"schema_node_not_object:{_schema_path(path)}")
            return
        if not any(key in node for key in ("type", "anyOf", "$ref")):
            shape_errors.append(f"schema_type_missing:{_schema_path(path)}")
        if "const" in node:
            if "type" not in node:
                const_errors.append({"path": _schema_path(path), "error": "const_type_missing"})
            try:
                inferred = infer_const_json_type(node["const"])
                if "type" in node and not _const_type_matches(inferred, node["type"]):
                    const_errors.append({"path": _schema_path(path), "error": "const_type_mismatch"})
                if inferred in {"array", "object"}:
                    const_errors.append({"path": _schema_path(path), "error": "const_requires_lowering"})
            except ValueError as exc:
                const_errors.append({"path": _schema_path(path), "error": str(exc).removeprefix("provider_")})
        node_type = node.get("type")
        types = node_type if isinstance(node_type, list) else [node_type]
        if "type" in node and (
            not types or not all(isinstance(item, str) and item in ALLOWED_TYPES for item in types)
        ):
            type_errors.append({"path": _schema_path(path), "type": node_type})
        is_container = "object" in types or "array" in types
        next_depth = nesting_depth + (1 if is_container else 0)
        max_nesting_depth = max(max_nesting_depth, next_depth)

        properties = node.get("properties")
        if "object" in types and not isinstance(properties, Mapping):
            object_errors.append({"path": _schema_path(path), "errors": ["object_properties_missing"]})
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
        if "$defs" in node and not isinstance(definitions, Mapping):
            shape_errors.append(f"definitions_not_object:{_schema_path(path)}")
        if isinstance(definitions, Mapping):
            schema_string_budget += sum(len(str(name)) for name in definitions)
            for name, child in definitions.items():
                visit(child, (*path, "$defs", str(name)), nesting_depth)

        items = node.get("items")
        if "array" in types:
            if not isinstance(items, Mapping):
                array_errors.append({"path": _schema_path(path), "error": "array_items_missing"})
        elif "items" in node:
            shape_errors.append(f"items_without_array_type:{_schema_path(path)}")
        if "items" in node:
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
        if "anyOf" in node and not isinstance(branches, list):
            shape_errors.append(f"anyof_not_array:{_schema_path(path)}")
        if isinstance(branches, list):
            if not branches:
                shape_errors.append(f"anyof_empty:{_schema_path(path)}")
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
    errors.extend(f"{row['error']}:{row['path']}" for row in const_errors)
    errors.extend(shape_errors)
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
        "const_errors": const_errors,
        "shape_errors": shape_errors,
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
