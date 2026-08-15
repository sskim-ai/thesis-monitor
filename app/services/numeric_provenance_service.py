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
        source = registry.get((fact_id, field_path))
        if source is None:
            errors.append(
                f"{prefix}:numeric_fact_ref_source_not_found:{ref_id}:{fact_id}:{field_path}"
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
        usage = f"{label} {display}"
        parent[child_key] = text.replace(placeholder, usage)
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
                "formatted_value": display,
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
        "bindings": bindings,
    }
    return NumericBindingResult(
        output=output,
        errors=tuple(dict.fromkeys(errors)),
        report=report,
    )
