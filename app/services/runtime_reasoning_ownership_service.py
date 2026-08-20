from __future__ import annotations

import copy
import re
from collections.abc import Mapping


NUMERIC_PRIMARY_OWNER_CONTRACT = "numeric-primary-owner-v1"
CURRENT_PRICE_RR_SEMANTIC = "current_price_risk_reward_ratio"
CURRENT_PRICE_RR_PRIMARY_TEXT_REF = "price_positioning.text"

_PATH_PART = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[([0-9]+)\])?$")


def _registry_semantics(packet: Mapping[str, object]) -> dict[str, dict[tuple[str, str], str]]:
    result: dict[str, dict[tuple[str, str], str]] = {}
    stocks = packet.get("stocks")
    if not isinstance(stocks, list):
        return result
    for stock in stocks:
        if not isinstance(stock, Mapping):
            continue
        ticker = str(stock.get("ticker") or "")
        rows: dict[tuple[str, str], str] = {}
        registry = stock.get("numeric_registry")
        if isinstance(registry, list):
            for item in registry:
                if not isinstance(item, Mapping):
                    continue
                rows[
                    (
                        str(item.get("fact_id") or ""),
                        str(item.get("field_path") or ""),
                    )
                ] = str(item.get("semantic_type") or "")
        result[ticker] = rows
    return result


def _text_node(review: dict[str, object], text_ref: str) -> tuple[dict[str, object], str] | None:
    value: object = review
    parts = text_ref.split(".")
    for raw_part in parts[:-1]:
        match = _PATH_PART.fullmatch(raw_part)
        if match is None or not isinstance(value, dict):
            return None
        value = value.get(match.group(1))
        if match.group(2) is not None:
            if not isinstance(value, list):
                return None
            index = int(match.group(2))
            if index >= len(value):
                return None
            value = value[index]
    terminal = _PATH_PART.fullmatch(parts[-1])
    if terminal is None or terminal.group(2) is not None or not isinstance(value, dict):
        return None
    return value, terminal.group(1)


def _remove_standalone_placeholder_sentence(text: str, ref_id: str) -> str | None:
    placeholder = re.escape(f"{{{{numeric:{ref_id}}}}}")
    pattern = re.compile(
        rf"(?:(?<=^)|(?<=[.!?])\s){placeholder}"
        rf"(?:입니다|이었습니다|였습니다)?[.!?]?(?=\s|$)"
    )
    match = pattern.search(text)
    if match is None:
        list_tail = re.compile(
            rf";\s*{placeholder}(?P<copula>입니다|이었습니다|였습니다)(?P<end>[.!?])"
        )
        tail_match = list_tail.search(text)
        if tail_match is None:
            return None
        return (
            text[: tail_match.start()]
            + tail_match.group("copula")
            + tail_match.group("end")
            + text[tail_match.end() :]
        )
    updated = (text[: match.start()] + text[match.end() :]).strip()
    return re.sub(r"[ \t]{2,}", " ", updated)


def apply_candidate_ownership_contracts(
    packet: Mapping[str, object],
    output_value: object,
) -> tuple[object, dict[str, object]]:
    """Deduplicate exact numeric owners only when the candidate is unambiguous."""
    if not isinstance(output_value, Mapping):
        return output_value, {
            "contract": NUMERIC_PRIMARY_OWNER_CONTRACT,
            "status": "not_applicable",
            "suppressions": [],
            "unresolved": [],
        }
    output = copy.deepcopy(dict(output_value))
    reviews = output.get("stock_reviews")
    if not isinstance(reviews, list):
        return output, {
            "contract": NUMERIC_PRIMARY_OWNER_CONTRACT,
            "status": "not_applicable",
            "suppressions": [],
            "unresolved": [],
        }
    semantics = _registry_semantics(packet)
    suppressions: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []
    for review in reviews:
        if not isinstance(review, dict):
            continue
        ticker = str(review.get("ticker") or "")
        refs = review.get("numeric_fact_refs")
        if not isinstance(refs, list):
            continue
        rr_refs = [
            item
            for item in refs
            if isinstance(item, dict)
            and semantics.get(ticker, {}).get(
                (
                    str(item.get("fact_id") or ""),
                    str(item.get("field_path") or ""),
                )
            )
            == CURRENT_PRICE_RR_SEMANTIC
        ]
        primary = [
            item
            for item in rr_refs
            if item.get("text_ref") == CURRENT_PRICE_RR_PRIMARY_TEXT_REF
        ]
        if len(primary) != 1:
            if rr_refs:
                unresolved.append(
                    {
                        "ticker": ticker,
                        "reason": "current_rr_primary_owner_missing_or_ambiguous",
                        "occurrence_count": len(rr_refs),
                        "primary_occurrence_count": len(primary),
                    }
                )
            continue
        removed_ids: set[str] = set()
        for item in rr_refs:
            text_ref = str(item.get("text_ref") or "")
            if text_ref == CURRENT_PRICE_RR_PRIMARY_TEXT_REF:
                continue
            ref_id = str(item.get("ref_id") or "")
            node = _text_node(review, text_ref)
            if node is None:
                unresolved.append(
                    {
                        "ticker": ticker,
                        "ref_id": ref_id,
                        "text_ref": text_ref,
                        "reason": "current_rr_secondary_text_ref_unresolved",
                    }
                )
                continue
            parent, key = node
            text = parent.get(key)
            updated = (
                _remove_standalone_placeholder_sentence(text, ref_id)
                if isinstance(text, str)
                else None
            )
            if updated is None:
                unresolved.append(
                    {
                        "ticker": ticker,
                        "ref_id": ref_id,
                        "text_ref": text_ref,
                        "reason": "current_rr_secondary_not_safely_removable",
                    }
                )
                continue
            parent[key] = updated
            removed_ids.add(ref_id)
            suppressions.append(
                {
                    "ticker": ticker,
                    "ref_id": ref_id,
                    "text_ref": text_ref,
                    "primary_text_ref": CURRENT_PRICE_RR_PRIMARY_TEXT_REF,
                    "reason": "current_rr_secondary_exact_occurrence",
                }
            )
        if removed_ids:
            review["numeric_fact_refs"] = [
                item
                for item in refs
                if not isinstance(item, dict)
                or str(item.get("ref_id") or "") not in removed_ids
            ]
    return output, {
        "contract": NUMERIC_PRIMARY_OWNER_CONTRACT,
        "status": "passed" if not unresolved else "unresolved",
        "suppressions": suppressions,
        "unresolved": unresolved,
    }
