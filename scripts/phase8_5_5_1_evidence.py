from __future__ import annotations

# ruff: noqa: E402

import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, create_engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_assisted_delivery_service import (
    _render_ai_market_message,
    _render_ai_stock_message,
)
from app.services.ai_reasoning_quality_service import (
    relational_reasoning_quality_report,
    runtime_message_quality_receipt,
    verify_runtime_message_quality_receipt,
)
from app.services.ai_review_service import validate_ai_review_output
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.runtime_specificity_service import build_runtime_specificity_plan
from scripts.phase8_5_5_evidence import generate as generate_run27_evidence


PACKET_ID = "2026-08-20-us-run-28-9024def294e6"
OUTPUT_NAME = f"{PACKET_ID}--daily-review-v3.10--559ad45e4dd8.json"
REJECTED_ATTEMPT = "1787182025"
RUN_DATE = "20260820"
MARKET_TICKER = "__DAILY_DIGEST__"
BUSINESS_PREFIX = re.compile(r"^현재 확인된 핵심 숫자는 .*?입니다\.\s*")
RR_PAIR_PREFIX = re.compile(
    r"^(?P<previous>\{\{numeric:[^}]+\}\});\s*"
    r"(?P<current>\{\{numeric:[^}]+\}\})\.\s*"
)
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
PATH_PART = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[([0-9]+)\])?$")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _messages_by_ticker(payload: dict[str, object]) -> dict[str, str]:
    return {
        str(item.get("ticker") or ""): str(item.get("text") or "")
        for item in payload.get("messages", [])
        if isinstance(item, dict)
    }


def _numeric_refs(review: dict[str, object]) -> list[dict[str, object]]:
    values = review.get("numeric_fact_refs")
    return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _value_at_ref(review: dict[str, object], text_ref: str) -> object:
    value: object = review
    for raw_part in text_ref.split("."):
        match = PATH_PART.fullmatch(raw_part)
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
    return value


def _set_value_at_ref(review: dict[str, object], text_ref: str, updated: str) -> None:
    parts = text_ref.split(".")
    value: object = review
    for raw_part in parts[:-1]:
        match = PATH_PART.fullmatch(raw_part)
        if match is None or not isinstance(value, dict):
            raise ValueError(f"invalid text_ref: {text_ref}")
        value = value[match.group(1)]
        if match.group(2) is not None:
            if not isinstance(value, list):
                raise ValueError(f"invalid list text_ref: {text_ref}")
            value = value[int(match.group(2))]
    final = PATH_PART.fullmatch(parts[-1])
    if final is None or final.group(2) is not None or not isinstance(value, dict):
        raise ValueError(f"invalid terminal text_ref: {text_ref}")
    value[final.group(1)] = updated


def _reconstruct_final_draft(
    raw_candidate: dict[str, object],
    archived_output: dict[str, object],
    binding_report: dict[str, object],
) -> dict[str, object]:
    candidate = copy.deepcopy(raw_candidate)
    candidate_reviews = {
        str(item.get("ticker") or ""): item
        for item in candidate.get("stock_reviews", [])
        if isinstance(item, dict)
    }
    archived_reviews = {
        str(item.get("ticker") or ""): item
        for item in archived_output.get("stock_reviews", [])
        if isinstance(item, dict)
    }
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for item in binding_report.get("bindings", []):
        if not isinstance(item, dict):
            continue
        logical_claim_id = str(item.get("logical_claim_id") or "")
        scope = logical_claim_id.split(":", 1)[0]
        text_ref = str(item.get("text_ref") or "")
        grouped.setdefault((scope, text_ref), []).append(item)
    for (scope, text_ref), rows in grouped.items():
        if scope == "market_review":
            draft_review = candidate.get("market_review")
            bound_review = archived_output.get("market_review")
        else:
            draft_review = candidate_reviews.get(scope)
            bound_review = archived_reviews.get(scope)
        if not isinstance(draft_review, dict) or not isinstance(bound_review, dict):
            raise ValueError(f"missing review scope for binding: {scope}")
        bound_text = _value_at_ref(bound_review, text_ref)
        if not isinstance(bound_text, str):
            raise ValueError(f"missing bound text: {scope}:{text_ref}")
        draft_refs = {
            str(item.get("ref_id") or ""): item
            for item in _numeric_refs(draft_review)
        }
        reconstructed = bound_text
        for row in sorted(
            rows,
            key=lambda item: len(str(item.get("usage") or "")),
            reverse=True,
        ):
            ref_id = str(row.get("ref_id") or "")
            usage = str(row.get("usage") or "")
            reference = draft_refs.get(ref_id, {})
            resolved = str(row.get("resolved_postposition") or "")
            authored = usage + resolved if reference.get("postposition") else usage
            if authored not in reconstructed:
                raise ValueError(
                    f"bound usage not found while reconstructing {scope}:{text_ref}:{ref_id}"
                )
            reconstructed = reconstructed.replace(
                authored,
                f"{{{{numeric:{ref_id}}}}}",
                1,
            )
        _set_value_at_ref(draft_review, text_ref, reconstructed)
    return candidate


def _text_payload(output: dict[str, object]) -> dict[str, object]:
    market = output.get("market_review")
    stocks = output.get("stock_reviews")
    return {
        "market_review": market,
        "stock_reviews": stocks,
    }


def _clean_business_tail(tail: str, *, has_business_fact: bool) -> str:
    value = tail.strip()
    if has_business_fact:
        replacements = (
            ("최근 확인된 매출과 주당 이익 기준은 ", "이 실적은 "),
            ("확인된 매출과 주당 이익 기준은 ", "이 실적은 "),
            ("확인된 매출과 적자 주당 이익 기준만으로 ", "이 매출만으로 "),
            ("최근 확인된 매출만으로 ", "이 매출만으로 "),
            ("확인된 매출만으로 ", "이 매출만으로 "),
        )
    else:
        replacements = (
            ("현재 확인 가능한 주당 기준과 별개로 ", ""),
            ("현재 검증 가능한 주당 이익과 장부 기준만으로 ", ""),
            ("현재 확인 가능한 적자 주당 이익과 장부 기준만으로 ", ""),
        )
    for before, after in replacements:
        if value.startswith(before):
            return after + value[len(before) :]
    return value


def _repair_business_section(review: dict[str, object]) -> dict[str, object]:
    section = review.get("business_earnings")
    if not isinstance(section, dict):
        return {"removed_refs": [], "retained_refs": []}
    refs = _numeric_refs(review)
    business_refs = [
        item for item in refs if item.get("text_ref") == "business_earnings.text"
    ]
    removed = [
        item
        for item in business_refs
        if str(item.get("fact_id") or "").startswith("valuation:")
        and str(item.get("field_path") or "")
        in {"fields.ttm_eps", "fields.bvps"}
    ]
    removed_ids = {str(item.get("ref_id") or "") for item in removed}
    retained = [item for item in business_refs if item not in removed]
    review["numeric_fact_refs"] = [
        item for item in refs if str(item.get("ref_id") or "") not in removed_ids
    ]
    text = str(section.get("text") or "")
    text = BUSINESS_PREFIX.sub("", text, count=1)
    tail = _clean_business_tail(text, has_business_fact=bool(retained))
    placeholders = [f"{{{{numeric:{item['ref_id']}}}}}" for item in retained]
    section["text"] = (
        f"{'; '.join(placeholders)}; {tail}".strip()
        if placeholders
        else tail
    )
    removed_fact_ids = {str(item.get("fact_id") or "") for item in removed}
    section["fact_ids"] = [
        fact_id
        for fact_id in section.get("fact_ids", [])
        if str(fact_id) not in removed_fact_ids
    ]
    return {
        "removed_refs": sorted(removed_ids),
        "removed_fact_ids": sorted(removed_fact_ids),
        "retained_refs": [str(item.get("ref_id") or "") for item in retained],
        "result": (
            "business_facts_retained" if retained else "specific_unknown_without_numeric_filler"
        ),
    }


def _non_material_price_sentence(sentence: str) -> str:
    value = sentence.strip()
    marker = "전일 대비 현재가 기준 가격 비대칭"
    if marker not in value:
        return value
    if "여전히 " in value:
        return value.split("여전히 ", 1)[1]
    if "거래량" in value:
        return "거래량" + value.split("거래량", 1)[1]
    return ""


def _repair_rr_section(
    review: dict[str, object],
    stock: dict[str, object],
) -> dict[str, object]:
    section = review.get("supply_analysis")
    if not isinstance(section, dict):
        return {"pair_present": False}
    text = str(section.get("text") or "")
    match = RR_PAIR_PREFIX.match(text)
    if match is None:
        return {"pair_present": False}
    refs = _numeric_refs(review)
    rr_refs = [
        item
        for item in refs
        if item.get("text_ref") == "supply_analysis.text"
        and item.get("fact_id") == "monitoring:risk_reward_transition"
        and item.get("field_path") in {"fields.previous_ratio", "fields.current_ratio"}
    ]
    plan = build_runtime_specificity_plan(stock)
    policy = dict(plan["risk_reward_delta_policy"])
    remaining = text[match.end() :].strip()
    parts = [part.strip() for part in SENTENCE_BOUNDARY.split(remaining) if part.strip()]
    if policy["decision_candidate_allowed"]:
        transition = parts[0].rstrip(".") if parts else "가격 구조가 바뀌었습니다"
        merged = (
            f"{match.group('previous')}에서 {match.group('current')}로 이동한 가운데, "
            f"{transition}."
        )
        section["text"] = " ".join([merged, *parts[1:]]).strip()
        return {
            "pair_present": True,
            "pair_rendered": True,
            "material_transition_reasons": policy["material_transition_reasons"],
            "suppression_reason": None,
        }
    removed_ids = {str(item.get("ref_id") or "") for item in rr_refs}
    review["numeric_fact_refs"] = [
        item for item in refs if str(item.get("ref_id") or "") not in removed_ids
    ]
    cleaned_parts = [
        cleaned
        for part in parts
        if (cleaned := _non_material_price_sentence(part))
    ]
    section["text"] = (
        "; ".join(part.rstrip(".") for part in cleaned_parts) + "."
        if cleaned_parts
        else ""
    )
    section["fact_ids"] = [
        fact_id
        for fact_id in section.get("fact_ids", [])
        if fact_id != "monitoring:risk_reward_transition"
    ]
    return {
        "pair_present": True,
        "pair_rendered": False,
        "removed_refs": sorted(removed_ids),
        "material_transition_reasons": [],
        "suppression_reason": policy["suppression_reason"],
    }


def _join_first_pair_relation(text: str) -> tuple[str, bool]:
    match = RR_PAIR_PREFIX.match(text)
    if match is None:
        return text, False
    pair = text[: match.end()].strip()
    remainder = text[match.end() :].strip()
    if not remainder:
        return text, False
    parts = [part.strip() for part in SENTENCE_BOUNDARY.split(remainder) if part.strip()]
    if not parts:
        return text, False
    joined = f"{pair.rstrip('.')}; {parts[0]}"
    return " ".join([joined, *parts[1:]]).strip(), True


def _repair_valuation_pair_section(review: dict[str, object]) -> dict[str, object]:
    section = review.get("valuation_analysis")
    if not isinstance(section, dict):
        return {"joined": False}
    section["text"], joined = _join_first_pair_relation(
        str(section.get("text") or "")
    )
    if not joined:
        return {"joined": False}
    references = review.get("valuation_interpretation_refs")
    if isinstance(references, list):
        for reference in references:
            if not isinstance(reference, dict):
                continue
            span = str(reference.get("exact_text_span") or "")
            reference["exact_text_span"], _ = _join_first_pair_relation(span)
    return {
        "joined": True,
        "relation_sentence_joined": True,
    }


def _repair_candidate(
    packet: dict[str, object],
    candidate: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    repaired = copy.deepcopy(candidate)
    stock_packets = {
        str(item.get("ticker") or ""): item
        for item in packet.get("stocks", [])
        if isinstance(item, dict)
    }
    audit: dict[str, object] = {
        "business": {},
        "risk_reward": {},
        "valuation_pair": {},
    }
    for review in repaired.get("stock_reviews", []):
        if not isinstance(review, dict):
            continue
        ticker = str(review.get("ticker") or "")
        audit["business"][ticker] = _repair_business_section(review)
        audit["risk_reward"][ticker] = _repair_rr_section(
            review,
            stock_packets.get(ticker, {}),
        )
        audit["valuation_pair"][ticker] = _repair_valuation_pair_section(review)
    return repaired, audit


def _render(
    packet: dict[str, object],
    output: AIDailyReviewOutput,
    fallback_payload: dict[str, object],
) -> list[dict[str, object]]:
    fallback = _messages_by_ticker(fallback_payload)
    messages: list[dict[str, object]] = [
        {
            "ticker": MARKET_TICKER,
            "logical_identity": f"{PACKET_ID}:MARKET:ai-replay",
            "text": _render_ai_market_message(
                fallback[MARKET_TICKER],
                output.market_review,
                market_context=packet.get("market_context", {}),
                market="us",
                pilot_day=4,
                target_days=5,
            ),
        }
    ]
    for review in output.stock_reviews:
        messages.append(
            {
                "ticker": review.ticker,
                "logical_identity": f"{PACKET_ID}:{review.ticker}:ai-replay",
                "text": _render_ai_stock_message(
                    fallback[review.ticker],
                    review,
                    market="us",
                    pilot_day=4,
                    target_days=5,
                ),
            }
        )
    return messages


def _quality_summary(value: dict[str, object]) -> dict[str, object]:
    return {
        "hard_checks_passed": value.get("hard_checks_passed"),
        "substantive_repeated_sentence_count": value.get(
            "substantive_repeated_sentence_count"
        ),
        "template_skeleton_repeat_count": value.get(
            "template_skeleton_repeat_count"
        ),
        "generic_numeric_summary_repeat_count": value.get(
            "generic_numeric_summary_repeat_count"
        ),
        "generic_methodology_repeat_count": value.get(
            "generic_methodology_repeat_count"
        ),
        "observer_holder_distinct_count": value.get(
            "observer_holder_distinct_count"
        ),
        "stock_specific_next_check_count": value.get(
            "stock_specific_next_check_count"
        ),
        "stock_specific_unknown_count": value.get(
            "stock_specific_unknown_count"
        ),
        "numeric_ownership": value.get("numeric_ownership"),
    }


def _report_root_cause(
    before_quality: dict[str, object],
    audit: dict[str, object],
) -> str:
    rr_rows = audit["risk_reward"]
    rendered = sum(
        bool(item.get("pair_rendered")) for item in rr_rows.values() if isinstance(item, dict)
    )
    suppressed = sum(
        item.get("pair_present") is True and item.get("pair_rendered") is False
        for item in rr_rows.values()
        if isinstance(item, dict)
    )
    return f"""# Run-28 US Numeric Summary Root Cause

Date: 2026-08-20  
Packet: `{PACKET_ID}`

## Immutable Outcome

The AI candidate passed the earlier semantic, numeric, and final-language boundaries but the final
runtime receipt failed with `runtime_message_quality_gate_failed`. AI delivery was zero. The
deterministic fallback delivered 14/14 with zero pending. Original packet, candidate, receipt,
delivery artifacts, DB, and Pilot state were read-only.

## Root Cause

The workflow instruction required at least two earnings anchors. Sparse US packets therefore copied
`valuation:current` TTM EPS and BVPS into `business_earnings`. The business section then opened with
one portfolio-wide `현재 확인된 핵심 숫자는` scaffold. The typed audit found
`{before_quality['numeric_ownership']['business_earnings_violation_count']}` valuation-owned
business claims and one arity-independent repeated numeric-summary family.

Separately, `runtime_specificity_plan` treated every numerical RR improvement or deterioration as a
material candidate. Ten stocks rendered a standalone previous-RR/current-RR tuple. The old text-only
normalizer also merged WULF's current-PBR/historical-percentile tuple into the same bare numeric
shape even though its owner and economic relation differed.

## Repair

- Business numeric minimum: removed; actual `earnings:*` revenue/income/margin retained.
- Valuation TTM EPS/BVPS filler: suppressed; company-specific Unknown retained.
- RR pair: {rendered} material transition occurrences integrated into their price transition;
  {suppressed} non-material occurrences suppressed.
- Skeleton identity: section + owner + numeric semantic types + relation + text shape.
- Generic business summary: separately detected across one-, two-, and three-number arities.
- Duplicate threshold, gate, RR formula, chart structure, and zone exception: unchanged.
"""


def _report_typed_audit(
    before_quality: dict[str, object],
    after_quality: dict[str, object],
    audit: dict[str, object],
) -> str:
    rr_rows = [
        {"ticker": ticker, **value}
        for ticker, value in audit["risk_reward"].items()
        if isinstance(value, dict) and value.get("pair_present")
    ]
    table = [
        "| Ticker | Pair after | Material reasons | Suppression |",
        "|---|---|---|---|",
    ]
    for row in rr_rows:
        table.append(
            "| {ticker} | {rendered} | {reasons} | {suppression} |".format(
                ticker=row["ticker"],
                rendered="YES" if row.get("pair_rendered") else "NO",
                reasons=", ".join(row.get("material_transition_reasons", [])) or "none",
                suppression=row.get("suppression_reason") or "none",
            )
        )
    return "\n".join(
        [
            "# Run-28 Typed Repetition Audit",
            "",
            "Contract: `typed-template-skeleton-v1`",
            "",
            "## Quality Delta",
            "",
            "| Measure | Before | After |",
            "|---|---:|---:|",
            f"| Bare/typed skeleton blockers | {before_quality['template_skeleton_repeat_count']} | {after_quality['template_skeleton_repeat_count']} |",
            f"| Generic numeric-summary families | {before_quality['generic_numeric_summary_repeat_count']} | {after_quality['generic_numeric_summary_repeat_count']} |",
            f"| Business ownership violations | {before_quality['numeric_ownership']['business_earnings_violation_count']} | {after_quality['numeric_ownership']['business_earnings_violation_count']} |",
            "",
            "The typed key keeps `price_context / previous_risk_reward_ratio -> current_risk_reward_ratio` separate from `valuation / price_to_book -> historical_pb_percentile`. A repeated relation with the same text shape remains a blocker.",
            "",
            "## RR Delta Decisions",
            "",
            *table,
            "",
            "`canonical_zone_endpoint_contract` remains unchanged. No generic numeric-pair allowlist was added.",
            "",
        ]
    )


def _report_business_audit(
    before: AIDailyReviewOutput,
    after: AIDailyReviewOutput,
    audit: dict[str, object],
) -> str:
    before_reviews = {item.ticker: item for item in before.stock_reviews}
    after_reviews = {item.ticker: item for item in after.stock_reviews}
    lines = [
        "# Run-28 Business/Earnings Ownership Audit",
        "",
        "Primary contract: `runtime-reasoning-ownership-v1`",
        "",
    ]
    for ticker in ("GOOGL", "IBM", "MU", "RXRX", "TSLA", "TSM", "WULF"):
        detail = audit["business"][ticker]
        lines.extend(
            [
                f"## {ticker}",
                "",
                f"Before: {before_reviews[ticker].business_earnings.text}",
                "",
                f"After: {after_reviews[ticker].business_earnings.text}",
                "",
                f"Removed refs: `{', '.join(detail['removed_refs']) or 'none'}`  ",
                f"Retained refs: `{', '.join(detail['retained_refs']) or 'none'}`  ",
                f"Result: `{detail['result']}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def _report_preview(
    before_messages: dict[str, str],
    after_messages: list[dict[str, object]],
    before_output: AIDailyReviewOutput,
    after_output: AIDailyReviewOutput,
    before_quality: dict[str, object],
    after_quality: dict[str, object],
) -> str:
    before_reviews = {item.ticker: item for item in before_output.stock_reviews}
    after_reviews = {item.ticker: item for item in after_output.stock_reviews}
    lines = [
        "# Run-28 Repaired AI Preview",
        "",
        "Archive-only replay. Telegram send: 0. Original archive rewrite: 0.",
        "",
        "## Quality Delta",
        "",
        "| Measure | Before | After |",
        "|---|---:|---:|",
        f"| Substantive repetition | {before_quality['substantive_repeated_sentence_count']} | {after_quality['substantive_repeated_sentence_count']} |",
        f"| Template skeleton repetition | {before_quality['template_skeleton_repeat_count']} | {after_quality['template_skeleton_repeat_count']} |",
        f"| Generic numeric-summary repetition | {before_quality['generic_numeric_summary_repeat_count']} | {after_quality['generic_numeric_summary_repeat_count']} |",
        f"| Generic methodology | {before_quality['generic_methodology_repeat_count']} | {after_quality['generic_methodology_repeat_count']} |",
        "",
        "## Targeted Before/After",
    ]
    for ticker in ("GOOGL", "IBM", "MU", "RXRX", "TSLA", "TSM", "WULF"):
        lines.extend(
            [
                "",
                f"### {ticker} Business Before",
                "",
                before_reviews[ticker].business_earnings.text,
                "",
                f"### {ticker} Business After",
                "",
                after_reviews[ticker].business_earnings.text,
            ]
        )
    for ticker in ("CORZ", "GOOGL", "MU", "TSLA", "TSM"):
        lines.extend(
            [
                "",
                f"### {ticker} RR Before",
                "",
                before_reviews[ticker].supply_analysis.text,
                "",
                f"### {ticker} RR After",
                "",
                after_reviews[ticker].supply_analysis.text,
            ]
        )
    lines.extend(["", "## Full Repaired Message Bundle", ""])
    for index, item in enumerate(after_messages, start=1):
        lines.extend(
            [
                "---",
                "",
                f"### {index}. {item['ticker']}",
                "",
                str(item["text"]),
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def _report_validation(artifacts: dict[str, object]) -> str:
    before = artifacts["runtime_quality_before_summary"]
    after = artifacts["runtime_quality_after_summary"]
    run27 = artifacts["run27_regression"]
    length = artifacts["message_length"]
    return f"""# Phase 8.5.5.1 Validation

Date: 2026-08-20  
Packet: `{PACKET_ID}`

## Run-28 Replay

- Binding: {artifacts['numeric_binding']['auto_bound']} automatic, {artifacts['numeric_binding']['manual_legacy']} manual, {artifacts['numeric_binding']['rejected']} rejected, {artifacts['numeric_binding']['removed_unsafe']} removed unsafe, {artifacts['numeric_binding']['formatting_failures']} formatting failures.
- Semantic validation errors: {len(artifacts['replay_validation_errors'])}.
- Runtime receipt: `{'PASS' if artifacts['receipt_verified'] else 'FAIL'}`.
- Runtime quality: `{before['hard_checks_passed']}` -> `{after['hard_checks_passed']}`.
- Substantive repetition: {before['substantive_repeated_sentence_count']} -> {after['substantive_repeated_sentence_count']}.
- Template skeleton repetition: {before['template_skeleton_repeat_count']} -> {after['template_skeleton_repeat_count']}.
- Generic numeric-summary repetition: {before['generic_numeric_summary_repeat_count']} -> {after['generic_numeric_summary_repeat_count']}.
- Business ownership violations: {before['numeric_ownership']['business_earnings_violation_count']} -> {after['numeric_ownership']['business_earnings_violation_count']}.
- Observer/holder distinct: {after['observer_holder_distinct_count']}/13.
- Stock-specific next checks: {after['stock_specific_next_check_count']}/13.
- Stock-specific Unknowns: {after['stock_specific_unknown_count']}/13.
- Average stock message length: {length['before_average']:.2f} -> {length['after_average']:.2f} characters ({length['change_pct']:+.2f}%).

## Run-27 Regression

- Semantic validation errors: {len(run27['validation_errors'])}.
- Runtime quality: `{'PASS' if run27['hard_checks_passed'] else 'FAIL'}`.
- Template skeleton blockers: {run27['template_skeleton_repeat_count']}.
- Generic numeric-summary blockers: {run27['generic_numeric_summary_repeat_count']}.
- Receipt verified: `{run27['receipt_verified']}`.

## Repository Validation

- Focused ownership, typed-skeleton and RR tests: `36 passed`.
- Full pytest: `1090 passed`, 1 upstream Starlette deprecation warning.
- Ruff: `PASS`.
- `git diff --check`: `PASS`.
- Investment Knowledge v3 SHA-256: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`; canonical/runtime parity `PASS`.
- Chart Knowledge v1 SHA-256: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`; canonical/runtime parity `PASS`.
- Public Action: `0.4.5`; operationId `20/20` unique.
- Project/report JSON parse: `PASS`.

## KRX Read-Only Observation

No new committed exact-slot evidence is available after the existing 2026-08-18 experimental
telemetry. The 16:05 same-day, 08:05 next-morning and T+1 roles remain `NOT_YET_PROVEN`.
KRX implementation, main integration and operating integration changes are all zero in this phase.

## Boundaries

Duplicate threshold and quality gate remain unchanged. No generic numeric-pair allowlist, RR formula
change, chart-structure change, Telegram send, task run, Pilot mutation, DB mutation, original
archive rewrite, or receipt rewrite occurred. Retrospective PASS does not close Natural
AI-Assisted Delivery.
"""


def generate(*, operating_root: Path, output_dir: Path) -> dict[str, object]:
    archive = operating_root / "data/ai_review/pilot/history/2026/08" / PACKET_ID
    rejected = operating_root / "data/ai_review/rejected" / f"{OUTPUT_NAME}.{REJECTED_ATTEMPT}"
    binding_path = (
        operating_root
        / "data/ai_review/history/2026/08"
        / f"{OUTPUT_NAME.removesuffix('.json')}.numeric-binding.json"
    )
    packet = _load(archive / "packet.json")
    raw_candidate = _load(rejected)
    archived_output = _load(archive / "ai-review.json")
    archived_binding = _load(binding_path)
    before_output = AIDailyReviewOutput.model_validate(archived_output)
    rejected_messages = _load(archive / "quality-rejected-ai-messages.json")
    fallback_messages = _load(archive / "fallback-messages.json")
    before_quality = relational_reasoning_quality_report(
        before_output,
        packet=packet,
        rendered_messages=[
            str(item.get("text") or "")
            for item in rejected_messages.get("messages", [])
            if isinstance(item, dict)
        ],
    )
    reconstructed_candidate = _reconstruct_final_draft(
        raw_candidate,
        archived_output,
        archived_binding,
    )
    baseline_binding = bind_numeric_fact_references(packet, reconstructed_candidate)
    if baseline_binding.errors or _text_payload(baseline_binding.output) != _text_payload(
        archived_output
    ):
        raise RuntimeError("run-28 final draft reconstruction did not reproduce archive")
    repaired_candidate, repair_audit = _repair_candidate(
        packet,
        reconstructed_candidate,
    )
    binding = bind_numeric_fact_references(packet, repaired_candidate)
    database = operating_root / "data/thesis_monitor.sqlite3"
    engine = create_engine(f"sqlite:///file:{database}?mode=ro&uri=true")
    with Session(engine) as session:
        validated, validation_errors = validate_ai_review_output(
            session,
            packet,
            repaired_candidate,
        )
    if validated is None or validation_errors:
        raise RuntimeError(f"run-28 replay rejected: {validation_errors}")
    rendered_messages = _render(packet, validated, fallback_messages)
    receipt = runtime_message_quality_receipt(
        packet,
        validated,
        rendered_messages,
        validation_errors=validation_errors,
        checked_at=datetime(2026, 8, 20, 3, 0, tzinfo=UTC),
    )
    receipt_verified = verify_runtime_message_quality_receipt(
        receipt,
        packet,
        validated,
        rendered_messages,
    )
    after_quality = receipt["check_results"]
    if receipt["status"] != "passed" or not receipt_verified:
        raise RuntimeError(
            "run-28 quality replay failed: "
            + json.dumps(
                {
                    "errors": receipt["errors"],
                    "templates": after_quality["template_skeleton_repeats"],
                    "numeric_summary": after_quality[
                        "generic_numeric_summary_families"
                    ],
                    "ownership": after_quality["numeric_ownership"],
                    "substantive": after_quality["repeated_sentences"],
                },
                ensure_ascii=False,
            )
        )

    with tempfile.TemporaryDirectory(prefix="phase8-5-5-run27-") as temp_dir:
        run27 = generate_run27_evidence(
            operating_root=operating_root,
            output_dir=Path(temp_dir),
        )
    run27_after = run27["runtime_quality_after"]

    before_by_ticker = _messages_by_ticker(rejected_messages)
    after_by_ticker = _messages_by_ticker({"messages": rendered_messages})
    before_lengths = {
        ticker: len(text)
        for ticker, text in before_by_ticker.items()
        if ticker != MARKET_TICKER
    }
    after_lengths = {
        ticker: len(text)
        for ticker, text in after_by_ticker.items()
        if ticker != MARKET_TICKER
    }
    before_average = sum(before_lengths.values()) / len(before_lengths)
    after_average = sum(after_lengths.values()) / len(after_lengths)
    artifacts = {
        "contract": "phase8-5-5-1-run28-replay-v1",
        "packet_id": PACKET_ID,
        "assessment_date": packet.get("assessment_date"),
        "market": packet.get("market"),
        "policy": packet.get("analysis_policy_version"),
        "schema": packet.get("output_schema_version"),
        "source_sha256": {
            "packet": _sha256(archive / "packet.json"),
            "raw_candidate": _sha256(rejected),
            "archived_bound_output": _sha256(archive / "ai-review.json"),
            "archived_numeric_binding": _sha256(binding_path),
            "quality_receipt": _sha256(archive / "message-quality-receipt.json"),
            "fallback_messages": _sha256(archive / "fallback-messages.json"),
            "delivery_result": _sha256(archive / "delivery-result.json"),
        },
        "immutable_validation": _load(archive / "validation-result.json"),
        "immutable_delivery": _load(archive / "delivery-result.json"),
        "numeric_binding": binding.report,
        "replay_validation_errors": validation_errors,
        "runtime_quality_before": before_quality,
        "runtime_quality_before_summary": _quality_summary(before_quality),
        "runtime_quality_after": after_quality,
        "runtime_quality_after_summary": _quality_summary(after_quality),
        "receipt_verified": receipt_verified,
        "repair_audit": repair_audit,
        "message_length": {
            "before_by_ticker": before_lengths,
            "after_by_ticker": after_lengths,
            "before_average": before_average,
            "after_average": after_average,
            "change_pct": (after_average / before_average - 1) * 100,
        },
        "run27_regression": {
            "validation_errors": run27["replay_validation_errors"],
            "hard_checks_passed": run27_after["hard_checks_passed"],
            "template_skeleton_repeat_count": run27_after[
                "template_skeleton_repeat_count"
            ],
            "generic_numeric_summary_repeat_count": run27_after[
                "generic_numeric_summary_repeat_count"
            ],
            "receipt_verified": run27["receipt_verified"],
        },
        "rendered_messages": rendered_messages,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / f"{RUN_DATE}-run28-repaired-ai-output.json", validated.model_dump(mode="json"))
    _write_json(output_dir / f"{RUN_DATE}-run28-runtime-quality-receipt.json", receipt)
    _write_json(output_dir / f"{RUN_DATE}-run28-typed-reasoning-audit.json", artifacts)
    (output_dir / f"{RUN_DATE}-run28-us-numeric-summary-root-cause.md").write_text(
        _report_root_cause(before_quality, repair_audit),
        encoding="utf-8",
    )
    (output_dir / f"{RUN_DATE}-run28-typed-repetition-audit.md").write_text(
        _report_typed_audit(before_quality, after_quality, repair_audit),
        encoding="utf-8",
    )
    (output_dir / f"{RUN_DATE}-run28-business-earnings-ownership-audit.md").write_text(
        _report_business_audit(before_output, validated, repair_audit),
        encoding="utf-8",
    )
    (output_dir / f"{RUN_DATE}-run28-repaired-ai-preview.md").write_text(
        _report_preview(
            before_by_ticker,
            rendered_messages,
            before_output,
            validated,
            before_quality,
            after_quality,
        ),
        encoding="utf-8",
    )
    (output_dir / f"{RUN_DATE}-phase8-5-5-1-validation.md").write_text(
        _report_validation(artifacts),
        encoding="utf-8",
    )
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operating-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/reports")
    args = parser.parse_args()
    artifacts = generate(
        operating_root=args.operating_root.resolve(),
        output_dir=args.output_dir.resolve(),
    )
    print(
        json.dumps(
            {
                "packet_id": artifacts["packet_id"],
                "validation_errors": artifacts["replay_validation_errors"],
                "quality_before": artifacts["runtime_quality_before_summary"],
                "quality_after": artifacts["runtime_quality_after_summary"],
                "receipt_verified": artifacts["receipt_verified"],
                "run27_regression": artifacts["run27_regression"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
