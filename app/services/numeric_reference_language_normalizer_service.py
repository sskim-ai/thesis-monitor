from __future__ import annotations

import copy
import re
from collections.abc import Mapping

from app.services.numeric_provenance_service import numeric_label_candidates


CONTRACT_VERSION = "numeric-reference-language-normalizer-v1"
_PLACEHOLDER = re.compile(r"\{\{numeric:([A-Za-z][A-Za-z0-9_-]{0,63})\}\}")
_PATH_PART = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[([0-9]+)\])?$")
_PARTICLE_FAMILY = {
    "은": "은/는",
    "는": "은/는",
    "이": "이/가",
    "가": "이/가",
    "을": "을/를",
    "를": "을/를",
    "와": "와/과",
    "과": "와/과",
}
_SAFE_COPULA = re.compile(r"^(?:이며|이고|이지만)")
_TYPED_SPAN_BRIDGE_REPAIRS = (
    (". 이 값은 이는 ", "이며, 이는 "),
)


def _text_target(review: dict[str, object], text_ref: str) -> tuple[dict[str, object], str] | None:
    node: object = review
    parts = text_ref.split(".")
    for raw_part in parts[:-1]:
        match = _PATH_PART.fullmatch(raw_part)
        if match is None or not isinstance(node, dict):
            return None
        key, index = match.groups()
        node = node.get(key)
        if index is not None:
            if not isinstance(node, list) or int(index) >= len(node):
                return None
            node = node[int(index)]
    if not isinstance(node, dict):
        return None
    final = _PATH_PART.fullmatch(parts[-1])
    if final is None or final.group(2) is not None:
        return None
    key = final.group(1)
    return (node, key) if isinstance(node.get(key), str) else None


def _strip_redundant_label(
    text: str,
    marker_start: int,
    source: dict[str, object],
    *,
    role: str,
) -> tuple[str, int, bool]:
    prefix = text[:marker_start]
    candidates = sorted(numeric_label_candidates(source, role=role), key=len, reverse=True)
    for candidate in candidates:
        match = re.search(
            rf"(?P<label>{re.escape(candidate)})(?:은|는|이|가|을|를|와|과)?\s*$",
            prefix,
            flags=re.IGNORECASE,
        )
        if match is None:
            continue
        if match.start() and prefix[match.start() - 1].isalnum():
            continue
        rewritten = prefix[: match.start()] + text[marker_start:]
        return rewritten, len(prefix[: match.start()]), True
    return text, marker_start, False


def _registry(context: object) -> dict[tuple[str, str], dict[str, object]]:
    if not isinstance(context, Mapping):
        return {}
    rows = context.get("numeric_registry")
    if not isinstance(rows, list):
        return {}
    return {
        (str(item.get("fact_id") or ""), str(item.get("field_path") or "")): dict(item)
        for item in rows
        if isinstance(item, Mapping)
    }


def _restore_structured_interpretation_spans(
    review: dict[str, object],
) -> list[dict[str, str]]:
    refs = review.get("valuation_interpretation_refs")
    if not isinstance(refs, list):
        return []
    repairs: list[dict[str, str]] = []
    for ref in refs:
        if not isinstance(ref, Mapping):
            continue
        text_ref = str(ref.get("text_ref") or "")
        exact_span = str(ref.get("exact_text_span") or "")
        target = _text_target(review, text_ref)
        if target is None or not exact_span or exact_span.count("{{numeric:") != 1:
            continue
        parent, key = target
        text = str(parent[key])
        if text.count(exact_span) == 1:
            continue
        for malformed_bridge, canonical_bridge in _TYPED_SPAN_BRIDGE_REPAIRS:
            if canonical_bridge not in exact_span:
                continue
            malformed_span = exact_span.replace(
                canonical_bridge,
                malformed_bridge,
                1,
            )
            if text.count(malformed_span) != 1:
                continue
            parent[key] = text.replace(malformed_span, exact_span, 1)
            repairs.append(
                {
                    "ref_id": str(ref.get("ref_id") or ""),
                    "text_ref": text_ref,
                    "reason": "structured_interpretation_span_restored",
                }
            )
            break
    return repairs


def normalize_numeric_reference_language(
    packet: Mapping[str, object],
    output_value: object,
) -> tuple[object, dict[str, object]]:
    """Apply one language-only normalization pass before canonical binding."""

    output = copy.deepcopy(output_value)
    if not isinstance(output, dict):
        return output, {
            "contract": CONTRACT_VERSION,
            "attempt_count": 0,
            "rewrite_count": 0,
            "invariant_errors": [],
        }
    packet_stocks = {
        str(item.get("ticker") or ""): item
        for item in packet.get("stocks", [])
        if isinstance(item, Mapping)
    }
    contexts: list[tuple[str, dict[str, object], object]] = []
    market_review = output.get("market_review")
    if isinstance(market_review, dict):
        contexts.append(("market_review", market_review, packet.get("market_context")))
    stock_reviews = output.get("stock_reviews")
    if isinstance(stock_reviews, list):
        contexts.extend(
            (
                str(review.get("ticker") or ""),
                review,
                packet_stocks.get(str(review.get("ticker") or "")),
            )
            for review in stock_reviews
            if isinstance(review, dict)
        )

    rewrites: list[dict[str, str]] = []
    invariant_errors: list[str] = []
    for scope, review, context in contexts:
        for repair in _restore_structured_interpretation_spans(review):
            rewrites.append({"scope": scope, **repair})
        refs = review.get("numeric_fact_refs")
        if not isinstance(refs, list):
            continue
        registry = _registry(context)
        before_identity = [
            tuple(str(item.get(key) or "") for key in ("ref_id", "fact_id", "field_path", "text_ref", "role"))
            for item in refs
            if isinstance(item, dict)
        ]
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            ref_id = str(ref.get("ref_id") or "")
            target = _text_target(review, str(ref.get("text_ref") or ""))
            source = registry.get(
                (str(ref.get("fact_id") or ""), str(ref.get("field_path") or ""))
            )
            if target is None or source is None:
                continue
            parent, key = target
            text = str(parent[key])
            placeholder = f"{{{{numeric:{ref_id}}}}}"
            if text.count(placeholder) != 1:
                continue
            marker_start = text.index(placeholder)
            rewritten, marker_start, label_removed = _strip_redundant_label(
                text,
                marker_start,
                source,
                role=str(ref.get("role") or "value"),
            )
            suffix = rewritten[marker_start + len(placeholder) :]
            particle_moved = False
            if not _SAFE_COPULA.match(suffix) and suffix[:1] in _PARTICLE_FAMILY:
                if not str(ref.get("postposition") or "").strip():
                    ref["postposition"] = _PARTICLE_FAMILY[suffix[0]]
                rewritten = (
                    rewritten[: marker_start + len(placeholder)]
                    + suffix[1:]
                )
                particle_moved = True
            if label_removed or particle_moved:
                parent[key] = rewritten
                rewrites.append(
                    {
                        "scope": scope,
                        "ref_id": ref_id,
                        "label_removed": str(label_removed).lower(),
                        "particle_moved": str(particle_moved).lower(),
                    }
                )
        after_identity = [
            tuple(str(item.get(key) or "") for key in ("ref_id", "fact_id", "field_path", "text_ref", "role"))
            for item in refs
            if isinstance(item, dict)
        ]
        if before_identity != after_identity:
            invariant_errors.append(f"{scope}:numeric_reference_identity_changed")
    return output, {
        "contract": CONTRACT_VERSION,
        "attempt_count": 1 if contexts else 0,
        "rewrite_count": len(rewrites),
        "rewrites": rewrites,
        "invariant_errors": invariant_errors,
        "class_ab_rerun_required": bool(rewrites),
    }
