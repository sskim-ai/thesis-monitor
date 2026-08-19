from __future__ import annotations

# ruff: noqa: E402

import argparse
import copy
import hashlib
import json
import re
import sys
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


PACKET_ID = "2026-08-19-kr-run-27-63a064e837ff"
OUTPUT_NAME = f"{PACKET_ID}--daily-review-v3.10--559ad45e4dd8.json"
REJECTED_ATTEMPT = "1787124206"
RUN_DATE = "20260819"
MARKET_TICKER = "__DAILY_DIGEST_KR__"
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n+")
TEXT_SECTIONS = (
    "core_judgment",
    "business_earnings",
    "price_positioning",
    "supply_analysis",
    "valuation_analysis",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text_nodes(review: dict[str, object]) -> list[tuple[dict[str, object], str]]:
    nodes: list[tuple[dict[str, object], str]] = []
    for key in TEXT_SECTIONS:
        value = review.get(key)
        if isinstance(value, dict):
            nodes.append((value, "text"))
    price = review.get("price_positioning")
    if isinstance(price, dict):
        nodes.extend(((price, "new_observer_view"), (price, "holder_view")))
    return nodes


def _remove_sentence(text: str, sentence: str) -> str:
    target = sentence.strip().casefold()
    for part in SENTENCE_BOUNDARY.split(text):
        if part.strip().casefold() == target:
            text = text.replace(part, "", 1)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _suppress_generic_portfolio_repeats(
    output: dict[str, object], report: dict[str, object]
) -> list[dict[str, object]]:
    repeated = {
        str(item.get("sentence") or "").casefold(): item
        for item in report.get("repeated_sentences", [])
        if isinstance(item, dict) and item.get("classification") == "substantive"
    }
    suppressions: list[dict[str, object]] = []
    reviews = output.get("stock_reviews")
    if not isinstance(reviews, list):
        return suppressions
    for review in reviews:
        if not isinstance(review, dict):
            continue
        ticker = str(review.get("ticker") or "")
        for node, key in _text_nodes(review):
            value = str(node.get(key) or "")
            for normalized, item in repeated.items():
                sentence = str(item.get("sentence") or "")
                updated = _remove_sentence(value, sentence)
                if updated != value:
                    suppressions.append(
                        {
                            "ticker": ticker,
                            "owner": "unknown_or_next_check",
                            "section": key,
                            "specificity_key": normalized,
                            "reason": "cross_ticker_generic_candidate",
                        }
                    )
                    value = updated
            node[key] = value
        for key in ("priority_watch", "next_checks", "unknowns"):
            values = review.get(key)
            if not isinstance(values, list):
                continue
            kept = []
            for value in values:
                if str(value).strip().casefold() in repeated:
                    suppressions.append(
                        {
                            "ticker": ticker,
                            "owner": "unknown_or_next_check",
                            "section": key,
                            "specificity_key": str(value).strip().casefold(),
                            "reason": "cross_ticker_generic_candidate",
                        }
                    )
                else:
                    kept.append(value)
            review[key] = kept
    return suppressions


def _harden_supply_relationship(review: dict[str, object]) -> bool:
    supply = review.get("supply_analysis")
    if not isinstance(supply, dict):
        return False
    text = str(supply.get("text") or "")
    parts = [part.strip() for part in text.splitlines() if part.strip()]
    if len(parts) < 4 or not all("{{numeric:" in part for part in parts[:-1]):
        return False
    relationship = parts[-1].rstrip(".")
    numeric_parts = [part.rstrip(".") for part in parts[:-1]]
    supply["text"] = f"{relationship}: " + "; ".join(numeric_parts) + "."
    return True


def _remove_postposition_before_predicate(review: dict[str, object]) -> list[str]:
    repaired: list[str] = []
    references = review.get("numeric_fact_refs")
    if not isinstance(references, list):
        return repaired
    for reference in references:
        if not isinstance(reference, dict):
            continue
        ref_id = str(reference.get("ref_id") or "")
        text_ref = str(reference.get("text_ref") or "")
        node: object = review
        for part in text_ref.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        if isinstance(node, str) and f"{{{{numeric:{ref_id}}}}}입니다" in node:
            reference.pop("postposition", None)
            repaired.append(ref_id)
    return repaired


def _framework_roles(stock: dict[str, object]) -> dict[str, list[str]]:
    routing = stock.get("knowledge_routing")
    if not isinstance(routing, dict):
        return {}
    industry = routing.get("industry_routing")
    primary = None
    secondary: list[str] = []
    if isinstance(industry, dict):
        primary = industry.get("primary_framework")
        secondary = [str(value) for value in industry.get("secondary_frameworks", [])]
    required = [str(value) for value in routing.get("required_frameworks", [])]
    chart_routing = stock.get("chart_knowledge_routing")
    chart_frameworks = (
        [str(value) for value in chart_routing.get("required_frameworks", [])]
        if isinstance(chart_routing, dict)
        else []
    )
    price_context = list(
        dict.fromkeys(
            [
                *[value for value in ("price_ohlcv", "holder_new_buyer") if value in required],
                *chart_frameworks,
            ]
        )
    )
    investment_industry = [
        value for value in [str(primary) if primary else "", *secondary] if value
    ]
    security_identity = [
        value for value in required if value in {"security_identity_v2", "adr_share_basis"}
    ]
    assigned = set(investment_industry) | set(price_context) | set(security_identity)
    return {
        "investment_industry": investment_industry,
        "price_context": price_context,
        "security_identity": security_identity,
        "general_reasoning": [value for value in required if value not in assigned],
    }


def _repair_candidate(
    packet: dict[str, object],
    candidate: dict[str, object],
    before_quality: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    repaired = copy.deepcopy(candidate)
    stock_packets = {
        str(item.get("ticker") or ""): item
        for item in packet.get("stocks", [])
        if isinstance(item, dict)
    }
    framework_suppressions: list[dict[str, object]] = []
    postposition_repairs: dict[str, list[str]] = {}
    supply_repairs: list[str] = []
    reviews = repaired.get("stock_reviews")
    if not isinstance(reviews, list):
        raise ValueError("run-27 candidate has no stock_reviews")
    for review in reviews:
        if not isinstance(review, dict):
            continue
        ticker = str(review.get("ticker") or "")
        stock = stock_packets.get(ticker, {})
        roles = _framework_roles(stock)
        allowed = {value for values in roles.values() for value in values}
        used = [str(value) for value in review.get("frameworks_used", [])]
        review["frameworks_used"] = [value for value in used if value in allowed]
        for value in used:
            if value not in review["frameworks_used"]:
                framework_suppressions.append(
                    {
                        "ticker": ticker,
                        "framework": value,
                        "owner": "price_context" if value == "chart_risk_reward" else "unknown",
                        "reason": "framework_not_available_in_packet_role",
                    }
                )
        refs = _remove_postposition_before_predicate(review)
        if refs:
            postposition_repairs[ticker] = refs
        if _harden_supply_relationship(review):
            supply_repairs.append(ticker)
    repeated_suppressions = _suppress_generic_portfolio_repeats(repaired, before_quality)
    return repaired, {
        "framework_suppressions": framework_suppressions,
        "postposition_repairs": postposition_repairs,
        "supply_relationship_first": supply_repairs,
        "candidate_suppressions": repeated_suppressions,
    }


def _messages_by_ticker(payload: dict[str, object]) -> dict[str, str]:
    return {
        str(item.get("ticker") or ""): str(item.get("text") or "")
        for item in payload.get("messages", [])
        if isinstance(item, dict)
    }


def _render(
    packet: dict[str, object],
    output: AIDailyReviewOutput,
    fallback_payload: dict[str, object],
) -> list[dict[str, object]]:
    fallback = _messages_by_ticker(fallback_payload)
    market_text = _render_ai_market_message(
        fallback[MARKET_TICKER],
        output.market_review,
        market_context=packet.get("market_context", {}),
        market="kr",
        pilot_day=4,
        target_days=5,
    )
    messages: list[dict[str, object]] = [
        {
            "ticker": MARKET_TICKER,
            "logical_identity": f"{PACKET_ID}:MARKET:ai-replay",
            "text": market_text,
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
                    market="kr",
                    pilot_day=4,
                    target_days=5,
                ),
            }
        )
    return messages


def _security_state(stock: dict[str, object]) -> tuple[str, str]:
    facts = stock.get("fact_catalog")
    if not isinstance(facts, list):
        return "unknown", "unknown"
    identity = next(
        (
            item
            for item in facts
            if isinstance(item, dict)
            and str(item.get("fact_id") or "").startswith("security_identity:")
        ),
        {},
    )
    fields = identity.get("fields") if isinstance(identity, dict) else {}
    if not isinstance(fields, dict):
        return "unknown", "unknown"
    return (
        str(
            fields.get("security_identity_state")
            or fields.get("identity_state")
            or fields.get("identity_status")
            or "unknown"
        ),
        str(fields.get("selected_security_type") or fields.get("security_type") or "unknown"),
    )


def _ownership_audit(
    packet: dict[str, object],
    raw_candidate: dict[str, object],
    repaired_candidate: dict[str, object],
    delta: dict[str, object],
) -> dict[str, object]:
    raw_reviews = {
        str(item.get("ticker") or ""): item
        for item in raw_candidate.get("stock_reviews", [])
        if isinstance(item, dict)
    }
    repaired_reviews = {
        str(item.get("ticker") or ""): item
        for item in repaired_candidate.get("stock_reviews", [])
        if isinstance(item, dict)
    }
    stocks = []
    for stock in packet.get("stocks", []):
        if not isinstance(stock, dict):
            continue
        ticker = str(stock.get("ticker") or "")
        identity_state, security_type = _security_state(stock)
        roles = _framework_roles(stock)
        raw_frameworks = [
            str(value) for value in raw_reviews.get(ticker, {}).get("frameworks_used", [])
        ]
        after_frameworks = [
            str(value) for value in repaired_reviews.get(ticker, {}).get("frameworks_used", [])
        ]
        stocks.append(
            {
                "ticker": ticker,
                "security_identity": {
                    "state": identity_state,
                    "security_type": security_type,
                    "depositary_reasoning_allowed": identity_state == "verified_depositary",
                    "suppression_reason": None
                    if identity_state == "verified_depositary"
                    else "security_identity_not_depositary",
                },
                "framework_roles": roles,
                "frameworks_before": raw_frameworks,
                "frameworks_after": after_frameworks,
                "chart_risk_reward_owner": "price_context",
                "chart_risk_reward_industry_framework": False,
            }
        )
    return {
        "contract": "runtime-reasoning-ownership-v1",
        "packet_id": PACKET_ID,
        "stocks": stocks,
        "suppression_delta": delta,
    }


def _preview_markdown(
    before_messages: dict[str, str],
    after_messages: dict[str, str],
    before_quality: dict[str, object],
    after_quality: dict[str, object],
) -> str:
    sections = [
        "# Run-27 Repaired AI Preview",
        "",
        "Archive-only replay. Telegram send: 0. Original archive rewrite: 0.",
        "",
        "## Portfolio Quality Delta",
        "",
        "| Measure | Before | After |",
        "|---|---:|---:|",
        f"| Substantive repetition | {before_quality['substantive_repeated_sentence_count']} | {after_quality['substantive_repeated_sentence_count']} |",
        f"| Template skeleton repetition | {before_quality['template_skeleton_repeat_count']} | {after_quality['template_skeleton_repeat_count']} |",
        f"| Generic methodology repetition | {before_quality['generic_methodology_repeat_count']} | {after_quality['generic_methodology_repeat_count']} |",
        f"| Runtime quality | FAIL | {'PASS' if after_quality['hard_checks_passed'] else 'FAIL'} |",
    ]
    for ticker in ("003690", "005490", "086280", "005930"):
        sections.extend(
            [
                "",
                f"## {ticker} Before",
                "",
                before_messages[ticker],
                "",
                f"## {ticker} After",
                "",
                after_messages[ticker],
            ]
        )
    return "\n".join(sections) + "\n"


def generate(*, operating_root: Path, output_dir: Path) -> dict[str, object]:
    archive = operating_root / "data/ai_review/pilot/history/2026/08" / PACKET_ID
    rejected = operating_root / "data/ai_review/rejected" / f"{OUTPUT_NAME}.{REJECTED_ATTEMPT}"
    packet = _load(archive / "packet.json")
    raw_candidate = _load(rejected)
    archived_output = AIDailyReviewOutput.model_validate(_load(archive / "ai-review.json"))
    rejected_messages = _load(archive / "quality-rejected-ai-messages.json")
    fallback_messages = _load(archive / "fallback-messages.json")
    before_quality = relational_reasoning_quality_report(
        archived_output,
        packet=packet,
        rendered_messages=[
            str(item.get("text") or "")
            for item in rejected_messages.get("messages", [])
            if isinstance(item, dict)
        ],
    )
    repaired_candidate, repair_delta = _repair_candidate(packet, raw_candidate, before_quality)
    binding = bind_numeric_fact_references(packet, repaired_candidate)
    database = operating_root / "data/thesis_monitor.sqlite3"
    engine = create_engine(f"sqlite:///file:{database}?mode=ro&uri=true")
    with Session(engine) as session:
        validated, validation_errors = validate_ai_review_output(
            session, packet, repaired_candidate
        )
    if validated is None or validation_errors:
        raise RuntimeError(f"run-27 replay rejected: {validation_errors}")
    rendered_messages = _render(packet, validated, fallback_messages)
    receipt = runtime_message_quality_receipt(
        packet,
        validated,
        rendered_messages,
        validation_errors=validation_errors,
        checked_at=datetime(2026, 8, 19, 12, 0, tzinfo=UTC),
    )
    if not verify_runtime_message_quality_receipt(receipt, packet, validated, rendered_messages):
        raise RuntimeError("run-27 replay receipt verification failed")
    after_quality = receipt["check_results"]
    before_by_ticker = _messages_by_ticker(rejected_messages)
    after_by_ticker = _messages_by_ticker({"messages": rendered_messages})
    before_lengths = {
        ticker: len(text) for ticker, text in before_by_ticker.items() if ticker != MARKET_TICKER
    }
    after_lengths = {
        ticker: len(text) for ticker, text in after_by_ticker.items() if ticker != MARKET_TICKER
    }
    ownership = _ownership_audit(packet, raw_candidate, repaired_candidate, repair_delta)
    artifacts = {
        "contract": "phase8-5-5-run27-replay-v1",
        "packet_id": PACKET_ID,
        "assessment_date": packet.get("assessment_date"),
        "market": packet.get("market"),
        "policy": packet.get("analysis_policy_version"),
        "schema": packet.get("output_schema_version"),
        "source_sha256": {
            "packet": _sha256(archive / "packet.json"),
            "raw_candidate": _sha256(rejected),
            "archived_bound_output": _sha256(archive / "ai-review.json"),
            "quality_receipt": _sha256(archive / "message-quality-receipt.json"),
            "fallback_messages": _sha256(archive / "fallback-messages.json"),
            "delivery_result": _sha256(archive / "delivery-result.json"),
        },
        "immutable_delivery": _load(archive / "delivery-result.json"),
        "immutable_validation": _load(archive / "validation-result.json"),
        "initial_errors": _load(Path(f"{rejected}.validation.json")).get("errors", []),
        "replay_validation_errors": validation_errors,
        "numeric_binding": binding.report,
        "runtime_quality_before": before_quality,
        "runtime_quality_after": after_quality,
        "receipt_verified": True,
        "message_length": {
            "before_by_ticker": before_lengths,
            "after_by_ticker": after_lengths,
            "before_average": sum(before_lengths.values()) / len(before_lengths),
            "after_average": sum(after_lengths.values()) / len(after_lengths),
        },
        "ownership": ownership,
        "rendered_messages": rendered_messages,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        output_dir / f"{RUN_DATE}-run27-repaired-ai-output.json", validated.model_dump(mode="json")
    )
    _write_json(output_dir / f"{RUN_DATE}-run27-runtime-quality-receipt.json", receipt)
    _write_json(output_dir / f"{RUN_DATE}-run27-reasoning-ownership-audit.json", artifacts)
    (output_dir / f"{RUN_DATE}-run27-repaired-ai-preview.md").write_text(
        _preview_markdown(before_by_ticker, after_by_ticker, before_quality, after_quality),
        encoding="utf-8",
    )
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--operating-root",
        type=Path,
        default=Path("/Users/sskim/Codex/thesis-monitor"),
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/reports")
    args = parser.parse_args()
    result = generate(
        operating_root=args.operating_root.resolve(),
        output_dir=args.output_dir.resolve(),
    )
    print(
        json.dumps(
            {
                "packet_id": result["packet_id"],
                "validation_errors": result["replay_validation_errors"],
                "auto_bound": result["numeric_binding"]["auto_bound"],
                "quality_pass": result["runtime_quality_after"]["hard_checks_passed"],
                "receipt_verified": result["receipt_verified"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
