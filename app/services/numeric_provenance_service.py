from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Any

from app.services.numeric_semantic_registry import (
    canonical_display_value,
    semantic_spec,
)


NUMERIC_REFERENCE_FIELD = "numeric_fact_refs"
_REFERENCE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
_PATH_PART = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[([0-9]+)\])?$")
_PLACEHOLDER = re.compile(r"\{\{numeric:([A-Za-z][A-Za-z0-9_-]{0,63})\}\}")
_ANY_PLACEHOLDER = re.compile(r"\{\{numeric:[^}]*\}\}")
_LABEL_SPACE = re.compile(r"\s+")
_KOREAN_PARTICLE = r"(?:은|는|이|가|을|를|와|과)?"
_ZONE_ROLE_PATH = re.compile(r"(?:^|\.)(?:zone|support_zone|box)_(low|high)$")
_RAW_POSTPOSITION = re.compile(r"^(은|는|이|가|을|를|와|과)")
_POSTPOSITION_FAMILIES = {
    "은/는": "은",
    "는/은": "은",
    "이/가": "이",
    "가/이": "이",
    "을/를": "을",
    "를/을": "을",
    "와/과": "와",
    "과/와": "와",
}


@dataclass(frozen=True)
class NumericBindingResult:
    output: object
    errors: tuple[str, ...]
    report: dict[str, object]


def _text_target(
    review: dict[str, object],
    text_ref: str,
) -> tuple[dict[str, object] | list[object], str | int, str] | None:
    node: object = review
    parts = text_ref.split(".")
    for index, raw_part in enumerate(parts):
        match = _PATH_PART.fullmatch(raw_part)
        if match is None:
            return None
        key, list_index = match.groups()
        if not isinstance(node, dict) or key not in node:
            return None
        parent: dict[str, object] | list[object] = node
        child_key: str | int = key
        node = node[key]
        if list_index is not None:
            if not isinstance(node, list):
                return None
            numeric_index = int(list_index)
            if numeric_index >= len(node):
                return None
            parent = node
            child_key = numeric_index
            node = node[numeric_index]
        if index == len(parts) - 1:
            return (
                parent,
                child_key,
                node if isinstance(node, str) else "",
            )
    return None


def _canonical_label(source: dict[str, object], role: str) -> str | None:
    labels = source.get("approved_labels")
    if not isinstance(labels, list) or not labels:
        return None
    semantic_type = str(source.get("semantic_type") or "")
    value = float(source["value"])
    candidates = [str(item) for item in labels if str(item).strip()]
    source_label = str(source.get("canonical_label") or "").strip()
    if source_label:
        selected = source_label
    elif semantic_type.endswith(
        ("net_buy_qty", "net_buy_qty_5d", "net_buy_qty_20d")
    ):
        marker = "순매도" if value < 0 else "순매수"
        selected = next((item for item in candidates if marker in item), candidates[0])
    else:
        selected = candidates[0]
    if role == "lower":
        return f"{selected} 하단"
    if role == "upper":
        return f"{selected} 상단"
    return selected


def expected_numeric_role(source: dict[str, object]) -> str | None:
    match = _ZONE_ROLE_PATH.search(str(source.get("field_path") or ""))
    if match is None:
        return None
    return "lower" if match.group(1) == "low" else "upper"


def _normalized_label(value: str) -> str:
    return _LABEL_SPACE.sub(" ", value.strip()).casefold()


def numeric_label_candidates(
    source: dict[str, object],
    *,
    role: str = "value",
) -> tuple[str, ...]:
    labels = source.get("approved_labels")
    candidates = (
        [str(item).strip() for item in labels if str(item).strip()]
        if isinstance(labels, list)
        else []
    )
    canonical = str(source.get("canonical_label") or "").strip()
    if canonical:
        candidates.insert(0, canonical)
    if role in {"lower", "upper"}:
        suffix = "하단" if role == "lower" else "상단"
        candidates = [f"{item} {suffix}" for item in candidates] + candidates
    return tuple(dict.fromkeys(candidates))


def redundant_numeric_label_before(
    text: str,
    marker_start: int,
    source: dict[str, object],
    *,
    role: str = "value",
) -> bool:
    prefix = _normalized_label(text[:marker_start])
    for candidate in numeric_label_candidates(source, role=role):
        label = _normalized_label(candidate)
        if not label:
            continue
        if re.search(
            rf"(?:^|[\s,;:()\[\]/]){re.escape(label)}{_KOREAN_PARTICLE}\s*$",
            prefix,
            flags=re.IGNORECASE,
        ):
            return True
    spec = semantic_spec(str(source.get("semantic_type") or ""))
    if spec is not None:
        tail = text[:marker_start].rstrip()[-96:]
        for pattern in spec.usage_patterns:
            if re.search(
                rf"(?:^|[\s,;:()\[\]/])(?:{pattern}){_KOREAN_PARTICLE}\s*$",
                tail,
                flags=re.IGNORECASE,
            ):
                return True
    return False


def _display_has_final_consonant(display: str) -> bool | None:
    normalized = display.strip()
    if not normalized:
        return None
    hangul_suffix = re.search(r"([가-힣])$", normalized)
    if hangul_suffix is not None:
        return (ord(hangul_suffix.group(1)) - ord("가")) % 28 != 0
    if normalized.endswith("%"):
        return False  # 퍼센트
    if re.search(r"bp$", normalized, flags=re.IGNORECASE):
        return False  # 비피
    if normalized.startswith(("$", "NT$")):
        return False  # 달러
    multiple_suffix = re.search(r"(?:x|배)$", normalized, flags=re.IGNORECASE)
    if multiple_suffix is not None:
        return False  # 배
    unit_letter = re.search(r"([A-Za-z])$", normalized)
    if unit_letter is not None:
        return unit_letter.group(1).upper() in {"F", "L", "M", "N", "R", "S", "X"}
    digit = re.search(r"([0-9])$", normalized)
    if digit is not None:
        return digit.group(1) in {"0", "1", "3", "6", "7", "8"}
    return None


def expected_numeric_postposition(display: str, particle: str) -> str | None:
    has_final_consonant = _display_has_final_consonant(display)
    if has_final_consonant is None or particle not in "은는이가을를와과":
        return None
    return {
        "은": "은" if has_final_consonant else "는",
        "는": "은" if has_final_consonant else "는",
        "이": "이" if has_final_consonant else "가",
        "가": "이" if has_final_consonant else "가",
        "을": "을" if has_final_consonant else "를",
        "를": "을" if has_final_consonant else "를",
        "와": "과" if has_final_consonant else "와",
        "과": "과" if has_final_consonant else "와",
    }[particle]


def resolve_numeric_postposition(display: str, family: str) -> str | None:
    """Resolve a typed Korean particle family from the backend-owned display phrase."""
    representative = _POSTPOSITION_FAMILIES.get(family.strip())
    if representative is None:
        return None
    return expected_numeric_postposition(display, representative)


def numeric_conjunction_error(text: str, usage: str, display: str) -> bool:
    start = text.find(usage)
    if start < 0:
        return False
    suffix = text[start + len(usage) :]
    if suffix.startswith(("가며", "가고")):
        return True
    if suffix.startswith(("이며", "이고")):
        return False
    particle = re.match(r"은|는|이|가|을|를|와|과", suffix)
    if particle is None:
        return False
    expected = expected_numeric_postposition(display, particle.group(0))
    if expected is None:
        return False
    return particle.group(0) != expected


def canonical_numeric_label_mismatch(
    source: dict[str, object],
    usage: str,
) -> str | None:
    if role := expected_numeric_role(source):
        expected = _normalized_label(str(_canonical_label(source, role) or ""))
        normalized_usage = _normalized_label(usage)
        if expected and not (
            normalized_usage == expected or normalized_usage.startswith(f"{expected} ")
        ):
            return "role"
    if source.get("canonical_label_required") is not True:
        return None
    canonical = _normalized_label(str(source.get("canonical_label") or ""))
    normalized_usage = _normalized_label(usage)
    if canonical and (
        normalized_usage == canonical or normalized_usage.startswith(f"{canonical} ")
    ):
        return None
    kind = str(source.get("canonical_label_kind") or "source")
    return kind if kind in {"instrument", "period"} else "source"


def _bound_label_quality_errors(
    review: dict[str, object],
    registry: dict[tuple[str, str], dict[str, object]],
    bindings: list[dict[str, object]],
    *,
    prefix: str,
) -> list[str]:
    errors: list[str] = []
    for binding in bindings:
        ref_id = str(binding["ref_id"])
        text_ref = str(binding["text_ref"])
        semantic_type = str(binding["semantic_type"])
        source = registry.get(
            (str(binding["fact_id"]), str(binding["field_path"]))
        )
        target = _text_target(review, text_ref)
        if source is None or target is None:
            continue
        text = target[2]
        usage = str(binding.get("usage") or "")
        mismatch = canonical_numeric_label_mismatch(source, usage)
        if mismatch is not None:
            errors.append(
                f"{prefix}:numeric_bound_{mismatch}_label_mismatch:"
                f"{ref_id}:{text_ref}:{semantic_type}"
            )
        if numeric_conjunction_error(
            text,
            usage,
            str(binding.get("formatted_value") or ""),
        ):
            errors.append(
                f"{prefix}:numeric_bound_postposition_mismatch:"
                f"{ref_id}:{text_ref}:{semantic_type}"
            )
        start = text.find(usage)
        if start >= 0 and redundant_numeric_label_before(
            text,
            start,
            source,
            role=str(binding.get("role") or "value"),
        ):
            errors.append(
                f"{prefix}:numeric_bound_repeated_label:"
                f"{ref_id}:{text_ref}:{semantic_type}"
            )
    return errors


def _bind_review(
    review: dict[str, object],
    registry_value: object,
    *,
    prefix: str,
    allowed_scopes: set[str],
) -> tuple[list[str], list[dict[str, object]], dict[str, int]]:
    errors: list[str] = []
    bindings: list[dict[str, object]] = []
    refs_value = review.pop(NUMERIC_REFERENCE_FIELD, [])
    claims = review.get("numeric_claims")
    if claims is None:
        claims = []
        review["numeric_claims"] = claims
    if not isinstance(claims, list):
        return (
            [f"{prefix}:numeric_binding_claims_not_list"],
            bindings,
            {"manual_legacy": 0, "auto_bound": 0, "formatting_failures": 0},
        )
    manual_legacy = len(claims)
    if refs_value is None:
        refs_value = []
    if not isinstance(refs_value, list):
        return (
            [f"{prefix}:numeric_fact_refs_not_list"],
            bindings,
            {
                "manual_legacy": manual_legacy,
                "auto_bound": 0,
                "formatting_failures": 0,
            },
        )
    registry = {
        (str(item.get("fact_id") or ""), str(item.get("field_path") or "")): item
        for item in registry_value
        if isinstance(item, dict)
    } if isinstance(registry_value, list) else {}
    facts_used = {
        str(item) for item in review.get("facts_used", [])
    } if isinstance(review.get("facts_used"), list) else set()
    seen_refs: set[str] = set()
    formatting_failures = 0
    for index, item in enumerate(refs_value):
        if not isinstance(item, dict):
            errors.append(f"{prefix}:numeric_fact_ref_not_object:{index}")
            continue
        ref_id = str(item.get("ref_id") or "")
        fact_id = str(item.get("fact_id") or "")
        field_path = str(item.get("field_path") or "")
        text_ref = str(item.get("text_ref") or "")
        role = str(item.get("role") or "value")
        postposition = str(item.get("postposition") or "").strip()
        if not _REFERENCE_ID.fullmatch(ref_id) or ref_id in seen_refs:
            errors.append(f"{prefix}:numeric_fact_ref_invalid_id:{ref_id or index}")
            continue
        seen_refs.add(ref_id)
        if role not in {"value", "lower", "upper"}:
            errors.append(f"{prefix}:numeric_fact_ref_invalid_role:{ref_id}:{role}")
            continue
        target = _text_target(review, text_ref)
        if target is None:
            errors.append(f"{prefix}:numeric_fact_ref_text_not_found:{ref_id}:{text_ref}")
            continue
        parent, child_key, text = target
        placeholder = f"{{{{numeric:{ref_id}}}}}"
        if text.count(placeholder) != 1:
            errors.append(
                f"{prefix}:numeric_fact_ref_placeholder_count:{ref_id}:"
                f"{text.count(placeholder)}"
            )
            continue
        marker_start = text.index(placeholder)
        raw_suffix = text[marker_start + len(placeholder) :]
        if _RAW_POSTPOSITION.match(raw_suffix):
            errors.append(
                f"{prefix}:numeric_fact_ref_raw_postposition:"
                f"{ref_id}:{text_ref}"
            )
            continue
        if postposition and postposition not in _POSTPOSITION_FAMILIES:
            errors.append(
                f"{prefix}:numeric_fact_ref_invalid_postposition:"
                f"{ref_id}:{postposition}"
            )
            continue
        source = registry.get((fact_id, field_path))
        if source is None:
            errors.append(
                f"{prefix}:numeric_fact_ref_source_not_found:{ref_id}:{fact_id}:{field_path}"
            )
            continue
        expected_role = expected_numeric_role(source)
        if expected_role is not None and role != expected_role:
            errors.append(
                f"{prefix}:numeric_fact_ref_zone_role_mismatch:"
                f"{ref_id}:{text_ref}:{source.get('semantic_type') or ''}:"
                f"{role}:{expected_role}"
            )
            continue
        if expected_role is None and role in {"lower", "upper"}:
            errors.append(
                f"{prefix}:numeric_fact_ref_unexpected_role:"
                f"{ref_id}:{text_ref}:{role}"
            )
            continue
        if fact_id not in facts_used:
            errors.append(f"{prefix}:numeric_fact_ref_fact_not_declared:{ref_id}:{fact_id}")
            continue
        if source.get("registered") is not True or source.get("prose_allowed") is not True:
            errors.append(
                f"{prefix}:numeric_fact_ref_semantic_not_supported:"
                f"{ref_id}:{fact_id}:{field_path}"
            )
            continue
        scope = str(source.get("scope") or "")
        if scope not in allowed_scopes:
            errors.append(
                f"{prefix}:numeric_fact_ref_scope_mismatch:{ref_id}:{scope}"
            )
            continue
        semantic_type = str(source.get("semantic_type") or "")
        spec = semantic_spec(semantic_type)
        if spec is None:
            errors.append(
                f"{prefix}:numeric_fact_ref_semantic_not_found:{ref_id}:{semantic_type}"
            )
            continue
        try:
            raw_value = float(source["value"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"{prefix}:numeric_fact_ref_value_invalid:{ref_id}")
            continue
        unit = str(source.get("unit") or "")
        display = canonical_display_value(spec, raw_value, unit)
        label = _canonical_label(source, role)
        if display is None or label is None:
            formatting_failures += 1
            errors.append(f"{prefix}:numeric_fact_ref_formatting_failed:{ref_id}")
            continue
        if redundant_numeric_label_before(
            text,
            marker_start,
            source,
            role=role,
        ):
            errors.append(
                f"{prefix}:numeric_fact_ref_redundant_authored_label:"
                f"{ref_id}:{text_ref}:{semantic_type}"
            )
            continue
        usage = f"{label} {display}"
        selected_postposition = (
            resolve_numeric_postposition(display, postposition)
            if postposition
            else None
        )
        if postposition and selected_postposition is None:
            errors.append(
                f"{prefix}:numeric_fact_ref_postposition_resolution_failed:"
                f"{ref_id}:{postposition}"
            )
            continue
        bound_text = text.replace(
            placeholder,
            usage + (selected_postposition or ""),
        )
        if numeric_conjunction_error(bound_text, usage, display):
            errors.append(
                f"{prefix}:numeric_fact_ref_postposition_mismatch:"
                f"{ref_id}:{text_ref}:{semantic_type}"
            )
            continue
        parent[child_key] = bound_text
        claim = {
            "fact_id": fact_id,
            "field_path": field_path,
            "value": source["value"],
            "unit": unit,
            "semantic_type": semantic_type,
            "text_ref": text_ref,
            "usage": usage,
        }
        claims.append(claim)
        logical_claim_id = f"{prefix}:{text_ref}:{fact_id}:{field_path}:{ref_id}"
        bindings.append(
            {
                "ref_id": ref_id,
                "logical_claim_id": logical_claim_id,
                "fact_id": fact_id,
                "field_path": field_path,
                "text_ref": text_ref,
                "semantic_type": semantic_type,
                "unit": unit,
                "role": role,
                "canonical_label": label,
                "canonical_label_kind": source.get("canonical_label_kind"),
                "formatted_value": display,
                "postposition_family": postposition or None,
                "resolved_postposition": selected_postposition,
                "usage": usage,
            }
        )
    leftovers = sorted(set(_ANY_PLACEHOLDER.findall(str(review))))
    for placeholder in leftovers:
        match = _PLACEHOLDER.fullmatch(placeholder)
        if match is not None and match.group(1) in seen_refs:
            continue
        unresolved = match.group(1) if match is not None else placeholder
        errors.append(
            f"{prefix}:numeric_fact_ref_unresolved_placeholder:{unresolved}"
        )
    errors.extend(
        _bound_label_quality_errors(
            review,
            registry,
            bindings,
            prefix=prefix,
        )
    )
    return (
        errors,
        bindings,
        {
            "manual_legacy": manual_legacy,
            "auto_bound": len(bindings),
            "formatting_failures": formatting_failures,
        },
    )


def bind_numeric_fact_references(
    packet: dict[str, object],
    output_value: object,
) -> NumericBindingResult:
    """Resolve draft-only numeric references into schema-4 prose and claims."""
    if not isinstance(output_value, dict):
        return NumericBindingResult(
            output=output_value,
            errors=(),
            report={
                "status": "not_applicable",
                "contract": "numeric-fact-ref-v1",
                "auto_bound": 0,
                "manual_legacy": 0,
                "rejected": 0,
                "removed_unsafe": 0,
                "formatting_failures": 0,
                "bindings": [],
            },
        )
    output = copy.deepcopy(output_value)
    errors: list[str] = []
    bindings: list[dict[str, object]] = []
    counters = {
        "auto_bound": 0,
        "manual_legacy": 0,
        "formatting_failures": 0,
    }
    market_review = output.get("market_review")
    market_context = packet.get("market_context")
    if isinstance(market_review, dict):
        market_errors, market_bindings, market_counts = _bind_review(
            market_review,
            market_context.get("numeric_registry")
            if isinstance(market_context, dict)
            else None,
            prefix="market_review",
            allowed_scopes={"market", "both"},
        )
        errors.extend(market_errors)
        bindings.extend(market_bindings)
        for key in counters:
            counters[key] += market_counts[key]
    packet_stocks = {
        str(item.get("ticker") or ""): item
        for item in packet.get("stocks", [])
        if isinstance(item, dict)
    }
    stock_reviews = output.get("stock_reviews")
    if isinstance(stock_reviews, list):
        for index, review in enumerate(stock_reviews):
            if not isinstance(review, dict):
                continue
            ticker = str(review.get("ticker") or f"stock_reviews[{index}]")
            stock = packet_stocks.get(ticker)
            stock_errors, stock_bindings, stock_counts = _bind_review(
                review,
                stock.get("numeric_registry") if isinstance(stock, dict) else None,
                prefix=ticker,
                allowed_scopes={"stock", "both"},
            )
            errors.extend(stock_errors)
            bindings.extend(stock_bindings)
            for key in counters:
                counters[key] += stock_counts[key]
    report: dict[str, Any] = {
        "status": "failed" if errors else "passed",
        "contract": "numeric-fact-ref-v1",
        **counters,
        "rejected": len(errors),
        "removed_unsafe": 0,
        "label_quality": {
            "redundant_authored_label_count": sum(
                "numeric_fact_ref_redundant_authored_label" in item
                for item in errors
            ),
            "repeated_bound_label_count": sum(
                "numeric_bound_repeated_label" in item for item in errors
            ),
            "source_label_mismatch_count": sum(
                "numeric_bound_source_label_mismatch" in item for item in errors
            ),
            "instrument_label_mismatch_count": sum(
                "numeric_bound_instrument_label_mismatch" in item
                for item in errors
            ),
            "period_label_mismatch_count": sum(
                "numeric_bound_period_label_mismatch" in item for item in errors
            ),
            "zone_role_mismatch_count": sum(
                "zone_role_mismatch" in item or "role_label_mismatch" in item
                for item in errors
            ),
            "postposition_mismatch_count": sum(
                "postposition_mismatch" in item for item in errors
            ),
        },
        "errors": list(dict.fromkeys(errors)),
        "bindings": bindings,
    }
    return NumericBindingResult(
        output=output,
        errors=tuple(dict.fromkeys(errors)),
        report=report,
    )
