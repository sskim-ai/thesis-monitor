"""Canonical deterministic schema validation, independent of proof controllers."""

from collections.abc import Mapping


def _resolve_ref(schema: Mapping[str, object], root: Mapping[str, object]) -> Mapping[str, object]:
    reference = schema.get("$ref")
    if not isinstance(reference, str):
        return schema
    if not reference.startswith("#/"):
        raise ValueError(f"unsupported_external_schema_ref:{reference}")
    value: object = root
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, Mapping) or token not in value:
            raise ValueError(f"unresolved_schema_ref:{reference}")
        value = value[token]
    if not isinstance(value, Mapping):
        raise ValueError(f"schema_ref_not_object:{reference}")
    return value


def validate_json_schema(
    instance: object,
    schema: Mapping[str, object],
    *,
    root: Mapping[str, object] | None = None,
    path: str = "$",
) -> list[str]:
    root = root or schema
    if "$ref" in schema:
        return validate_json_schema(instance, _resolve_ref(schema, root), root=root, path=path)
    if "anyOf" in schema:
        alternatives = schema["anyOf"]
        if not isinstance(alternatives, list):
            return [f"{path}:anyOf_not_array"]
        results = [
            validate_json_schema(instance, item, root=root, path=path)
            for item in alternatives
            if isinstance(item, Mapping)
        ]
        if any(not errors for errors in results):
            return []
        return [f"{path}:no_anyOf_match"]

    errors: list[str] = []
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}:const_mismatch")
    enum = schema.get("enum")
    if isinstance(enum, list) and instance not in enum:
        errors.append(f"{path}:enum_mismatch")
    expected_type = schema.get("type")
    type_ok = True
    if expected_type == "object":
        type_ok = isinstance(instance, Mapping)
    elif expected_type == "array":
        type_ok = isinstance(instance, list)
    elif expected_type == "string":
        type_ok = isinstance(instance, str)
    elif expected_type == "integer":
        type_ok = isinstance(instance, int) and not isinstance(instance, bool)
    elif expected_type == "number":
        type_ok = isinstance(instance, (int, float)) and not isinstance(instance, bool)
    elif expected_type == "boolean":
        type_ok = isinstance(instance, bool)
    elif expected_type == "null":
        type_ok = instance is None
    if expected_type is not None and not type_ok:
        return [f"{path}:type_mismatch:{expected_type}"]

    if isinstance(instance, Mapping):
        required = schema.get("required")
        if isinstance(required, list):
            errors.extend(
                f"{path}:missing_required:{key}" for key in required if key not in instance
            )
        properties = schema.get("properties")
        if isinstance(properties, Mapping):
            if schema.get("additionalProperties") is False:
                errors.extend(
                    f"{path}:additional_property:{key}" for key in instance if key not in properties
                )
            for key, value in instance.items():
                child = properties.get(key)
                if isinstance(child, Mapping):
                    errors.extend(
                        validate_json_schema(value, child, root=root, path=f"{path}.{key}")
                    )
    elif isinstance(instance, list):
        minimum = schema.get("minItems")
        maximum = schema.get("maxItems")
        if isinstance(minimum, int) and len(instance) < minimum:
            errors.append(f"{path}:minItems:{minimum}")
        if isinstance(maximum, int) and len(instance) > maximum:
            errors.append(f"{path}:maxItems:{maximum}")
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, value in enumerate(instance):
                errors.extend(
                    validate_json_schema(value, item_schema, root=root, path=f"{path}[{index}]")
                )
    elif isinstance(instance, str):
        minimum = schema.get("minLength")
        maximum = schema.get("maxLength")
        if isinstance(minimum, int) and len(instance) < minimum:
            errors.append(f"{path}:minLength:{minimum}")
        if isinstance(maximum, int) and len(instance) > maximum:
            errors.append(f"{path}:maxLength:{maximum}")
    return errors
