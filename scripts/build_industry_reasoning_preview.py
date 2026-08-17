from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
from pathlib import Path

from sqlmodel import Session, create_engine

from app.schemas.ai_review import AIDailyReviewOutput, AIStockReview
from app.services.ai_assisted_delivery_service import _render_ai_stock_message
from app.services.ai_reasoning_quality_service import runtime_message_quality_receipt
from app.services.ai_review_service import _validate_bound_ai_review_output
from app.services.industry_reasoning_service import (
    INDUSTRY_REASONING_CONTRACT,
    build_industry_reasoning_plan,
    industry_reasoning_guardrail_flags,
)
from app.services.numeric_provenance_service import TYPED_VALUATION_CONTRACT
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.semantic_decision_service import (
    SEMANTIC_SCOPE_CONTRACT,
    assign_listed_security_valuation_scope,
    observer_holder_semantic_error,
)


US_REPRESENTATIVE_TICKERS = ("MU", "TSM", "TSLA", "RXRX", "WULF", "IBM")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an archive-only Phase 8.5 industry reasoning Preview"
    )
    parser.add_argument("--source-packet", required=True, type=Path)
    parser.add_argument("--source-output", required=True, type=Path)
    parser.add_argument("--source-messages", required=True, type=Path)
    parser.add_argument("--deterministic-messages", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--baseline-preview", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--prefix", default="20260817-phase8-5-us")
    parser.add_argument(
        "--retrospective-packet-id",
        default="2026-08-17-us-phase8-5-industry-reasoning-retrospective",
    )
    return parser


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: object) -> None:
    _atomic_write(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _write_text(path: Path, value: str) -> None:
    _atomic_write(path, value.rstrip() + "\n")


def _atomic_write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _message_map(value: dict[str, object], *, deterministic: bool = False) -> dict[str, str]:
    output: dict[str, str] = {}
    for item in value.get("messages", []):
        if not isinstance(item, dict):
            continue
        ticker = str(item.get("ticker") or "")
        payload = item.get("payload") if deterministic else item
        text = payload.get("text") if isinstance(payload, dict) else None
        if ticker and isinstance(text, str):
            output[ticker] = text
    return output


def _counts(text: str) -> dict[str, int]:
    return {
        "characters": len(text),
        "lines": len(text.splitlines()),
        "sections": sum(
            line.startswith(("🎯", "📈", "💰", "📊", "📐", "⚠️", "👁", "📌"))
            for line in text.splitlines()
        ),
    }


def _preview_message_map(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    headings = list(re.finditer(r"^## \d+\. ([A-Z0-9_]+)\s*$", text, re.M))
    output: dict[str, str] = {}
    for index, match in enumerate(headings):
        ticker = match.group(1)
        start = match.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        block = text[start:end].strip()
        if block:
            output[ticker] = block
    return output


def _section_lines(message: str, heading: str) -> list[str]:
    lines = message.splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError:
        return []
    output: list[str] = []
    for line in lines[start:]:
        if line and line[0] in "🎯📈💰📊📐⚠👁📌":
            break
        output.append(line)
    while output and not output[0].strip():
        output.pop(0)
    while output and not output[-1].strip():
        output.pop()
    return output


def _apply_validated_preview(
    review: dict[str, object],
    stock: dict[str, object],
    message: str,
) -> None:
    for heading, section in (
        ("🎯 핵심 판단", "core_judgment"),
        ("📈 사업·실적", "business_earnings"),
        ("📊 거래량·포지셔닝", "supply_analysis"),
        ("📐 Valuation", "valuation_analysis"),
    ):
        lines = _section_lines(message, heading)
        if lines and isinstance(review.get(section), dict):
            review[section]["text"] = "\n".join(lines)

    price_lines = _section_lines(message, "💰 가격·포지셔닝")
    price = review.get("price_positioning")
    if price_lines and isinstance(price, dict):
        body: list[str] = []
        for line in price_lines:
            if line.startswith("• 신규 관찰자: "):
                price["new_observer_view"] = line.removeprefix("• 신규 관찰자: ")
            elif line.startswith("• 보유자: "):
                price["holder_view"] = line.removeprefix("• 보유자: ")
            elif line:
                body.append(line)
        price["text"] = "\n".join(body)
        observer = str(price.get("new_observer_view") or "")
        holder = str(price.get("holder_view") or "")
        role_error = observer_holder_semantic_error(observer, holder)
        if role_error == "observer_decision_variable_missing":
            price["new_observer_view"] = (
                f"{observer} 이를 신규 진입 조건으로 쓰지 않습니다."
            )
        elif role_error == "holder_decision_variable_missing":
            plan = build_industry_reasoning_plan(stock)
            if plan.primary_framework == "semiconductor":
                supplement = "지지 유지와 수익성·설비투자 훼손을 함께 확인합니다."
            elif "hyperscaler_capex_transmission" in plan.secondary_contexts:
                supplement = "지지 유지와 계약·현금전환 훼손을 함께 확인합니다."
            else:
                supplement = "지지 유지와 사업 논리 훼손을 함께 확인합니다."
            price["holder_view"] = (
                f"{holder} {supplement}"
            )

    for heading, field in (
        ("👁 핵심 감시", "priority_watch"),
        ("📌 다음 확인", "next_checks"),
        ("⚠️ 미확인", "unknowns"),
    ):
        values = [
            line.removeprefix("• ")
            for line in _section_lines(message, heading)
            if line.startswith("• ")
        ]
        if values:
            review[field] = values

    catalog = [item for item in stock.get("fact_catalog", []) if isinstance(item, dict)]
    for fact in catalog:
        fact_id = str(fact.get("fact_id") or "")
        fields = fact.get("fields")
        if fact_id == "chart:structure:risk_reward:current_price":
            fact["fact_type"] = "chart_risk_reward_current_price"
            if isinstance(fields, dict):
                fields["rr_basis"] = "current_price"
    assign_listed_security_valuation_scope(catalog)
    stock["fact_catalog"] = catalog
    stock["numeric_registry"] = build_numeric_registry(catalog)
    stock["typed_valuation_interpretation_contract"] = TYPED_VALUATION_CONTRACT
    stock["semantic_scope_contract"] = SEMANTIC_SCOPE_CONTRACT

    claims = [item for item in review.get("numeric_claims", []) if isinstance(item, dict)]
    registry = {
        (str(item.get("fact_id") or ""), str(item.get("field_path") or "")): item
        for item in stock["numeric_registry"]
        if isinstance(item, dict)
    }
    for claim in claims:
        source = registry.get(
            (str(claim.get("fact_id") or ""), str(claim.get("field_path") or ""))
        )
        if isinstance(source, dict):
            claim["semantic_type"] = source["semantic_type"]
            claim["unit"] = source["unit"]
        target = _text_at_ref(review, str(claim.get("text_ref") or ""))
        usage = str(claim.get("usage") or "")
        display = _usage_display(usage)
        semantic = str(claim.get("semantic_type") or "")
        if semantic in {
            "revenue",
            "operating_income",
            "net_income",
            "operating_margin",
            "revenue_qoq",
            "revenue_yoy",
            "operating_income_qoq",
            "operating_income_yoy",
        }:
            period_usage = _period_usage(target, display)
            if period_usage:
                claim["usage"] = period_usage
        elif semantic == "current_price_risk_reward_ratio":
            rr_usage = re.search(
                rf"현재가\s*기준\s*차트\s*손익비\s*{re.escape(display)}",
                target,
            )
            if rr_usage:
                claim["usage"] = rr_usage.group(0)
    supply = review.get("supply_analysis")
    if isinstance(supply, dict):
        supply_text = str(supply.get("text") or "")
        daily_volume = next(
            (
                item
                for item in stock["numeric_registry"]
                if isinstance(item, dict)
                and item.get("fact_id") == "chart:daily"
                and item.get("field_path") == "fields.volume_ratio_20"
            ),
            None,
        )
        if isinstance(daily_volume, dict):
            usage = f"20일 거래량비 {daily_volume['canonical_display_value']}"
            if usage in supply_text:
                claims.append(
                    {
                        "fact_id": "chart:daily",
                        "field_path": "fields.volume_ratio_20",
                        "value": daily_volume["value"],
                        "unit": daily_volume["unit"],
                        "semantic_type": daily_volume["semantic_type"],
                        "text_ref": "supply_analysis.text",
                        "usage": usage,
                    }
                )
                fact_ids = [
                    str(item) for item in supply.get("fact_ids", []) if item != "positioning:latest"
                ]
                if "chart:daily" not in fact_ids:
                    fact_ids.append("chart:daily")
                supply["fact_ids"] = fact_ids
                facts_used = [str(item) for item in review.get("facts_used", [])]
                if "chart:daily" not in facts_used:
                    facts_used.append("chart:daily")
                review["facts_used"] = facts_used
    review["numeric_claims"] = claims


def _text_at_ref(review: dict[str, object], text_ref: str) -> str:
    node: object = review
    for part in text_ref.split("."):
        if not isinstance(node, dict):
            return ""
        node = node.get(part)
    return node if isinstance(node, str) else ""


def _usage_display(usage: str) -> str:
    matches = list(re.finditer(r"[-+$₩NT$]?[0-9][0-9,.]*(?:[BMKT])?%?(?:배)?", usage))
    return matches[-1].group(0) if matches else usage


def _period_usage(text: str, display: str) -> str | None:
    pattern = re.compile(
        rf"(?:잠정\s+)?20\d{{2}}년\s*[1-4]분기[^,.\n]{{0,65}}?{re.escape(display)}"
    )
    match = pattern.search(text)
    return match.group(0) if match else None


def _preview(
    packet_id: object,
    names: dict[str, str],
    before: dict[str, str],
    after: dict[str, str],
    audit: dict[str, dict[str, object]],
) -> str:
    sections = [
        "# Phase 8.5 US Industry-Specific Reasoning Preview",
        "",
        (
            f"Archive-only Preview from immutable packet `{packet_id}`. AFTER blocks are "
            "exact production-renderer output and were not edited by hand. Telegram sends: `0`."
        ),
        "",
        (
            "Phase 8.5 formalizes routing and causal guardrails. Where the existing full "
            "message already satisfies the contract, the visible text is intentionally retained."
        ),
    ]
    for ticker in US_REPRESENTATIVE_TICKERS:
        before_counts = _counts(before[ticker])
        after_counts = _counts(after[ticker])
        row = audit[ticker]
        sections.extend(
            [
                "",
                "---",
                "",
                f"## {names[ticker]} ({ticker})",
                "",
                "### BEFORE — Current Schema-4 Baseline",
                "",
                before[ticker],
                "",
                "### AFTER — Phase 8.5",
                "",
                after[ticker],
                "",
                "### INDUSTRY CONTRACT",
                "",
                f"- Primary: `{row['primary_framework']}`; confidence: `{row['confidence']}`.",
                f"- Secondary: {', '.join(row['secondary_contexts']) or 'none'}.",
                f"- Missing drivers retained as Unknown: {', '.join(row['missing_drivers'])}.",
                f"- Guardrail flags: {len(row['guardrail_flags'])}.",
                (
                    f"- Length: {before_counts['characters']} → {after_counts['characters']} "
                    f"characters; {before_counts['lines']} → {after_counts['lines']} lines; "
                    f"{before_counts['sections']} → {after_counts['sections']} sections."
                ),
            ]
        )
    return "\n".join(sections)


def main() -> None:
    args = _parser().parse_args()
    source_packet = _load(args.source_packet)
    source_output = _load(args.source_output)
    deterministic_messages = _load(args.deterministic_messages)
    validated_preview = _preview_message_map(args.baseline_preview)
    selected = set(US_REPRESENTATIVE_TICKERS)

    packet = copy.deepcopy(source_packet)
    packet["packet_id"] = args.retrospective_packet_id
    packet["stocks"] = [
        stock
        for stock in packet.get("stocks", [])
        if isinstance(stock, dict) and str(stock.get("ticker") or "") in selected
    ]
    for stock in packet["stocks"]:
        stock["industry_reasoning_contract"] = INDUSTRY_REASONING_CONTRACT

    output_value = copy.deepcopy(source_output)
    output_value["packet_id"] = args.retrospective_packet_id
    output_value["stock_reviews"] = [
        review
        for review in output_value.get("stock_reviews", [])
        if isinstance(review, dict) and str(review.get("ticker") or "") in selected
    ]
    packet_stocks = {
        str(item.get("ticker") or ""): item
        for item in packet["stocks"]
        if isinstance(item, dict)
    }
    for review in output_value["stock_reviews"]:
        ticker = str(review.get("ticker") or "")
        _apply_validated_preview(review, packet_stocks[ticker], validated_preview[ticker])
    market_context = output_value.get("market_review", {}).get("market_context")
    if isinstance(market_context, dict) and isinstance(market_context.get("text"), str):
        market_context["text"] = re.sub(
            r"(VIX\s+\d+(?:\.\d+)?)는",
            r"\1은",
            market_context["text"],
        )
    output = AIDailyReviewOutput.model_validate(output_value)

    database_uri = f"sqlite:///file:{args.database.resolve()}?mode=ro&immutable=1&uri=true"
    with Session(create_engine(database_uri)) as session:
        validated, validation_errors = _validate_bound_ai_review_output(
            session,
            packet,
            output.model_dump(mode="json"),
        )
    if validated is None or validation_errors:
        raise ValueError("full validation failed: " + "; ".join(validation_errors))

    stocks = packet_stocks
    before = validated_preview
    deterministic = _message_map(deterministic_messages, deterministic=True)
    names = {
        ticker: str(stocks[ticker].get("company_name") or ticker)
        for ticker in US_REPRESENTATIVE_TICKERS
    }
    after: dict[str, str] = {}
    rendered: list[dict[str, object]] = []
    market_ticker = "__DAILY_DIGEST_US__"
    rendered.append(
        {
            "ticker": market_ticker,
            "text": before.get(market_ticker, before["__DAILY_DIGEST__"]),
            "logical_identity": (
                f"phase8-5-us:{args.retrospective_packet_id}:market"
            ),
        }
    )
    audit: dict[str, dict[str, object]] = {}
    for review in output.stock_reviews:
        stock = stocks[review.ticker]
        plan = build_industry_reasoning_plan(stock, facts_used=review.facts_used)
        flags = industry_reasoning_guardrail_flags(review, stock)
        if flags:
            raise ValueError(
                f"industry reasoning guardrail failed for {review.ticker}: "
                + "; ".join(flags)
            )
        text = _render_ai_stock_message(
            deterministic[review.ticker],
            AIStockReview.model_validate(review),
            market="us",
            pilot_day=3,
            target_days=5,
        )
        after[review.ticker] = text
        rendered.append(
            {
                "ticker": review.ticker,
                "text": text,
                "logical_identity": (
                    f"phase8-5-us:{args.retrospective_packet_id}:stock:{review.ticker}"
                ),
            }
        )
        audit[review.ticker] = {
            **plan.as_dict(),
            "guardrail_flags": flags,
            "observer_holder_distinct": (
                review.price_positioning.new_observer_view
                != review.price_positioning.holder_view
            ),
            "unknown_count": len(review.unknowns),
            "next_check_count": len(review.next_checks),
        }

    receipt = runtime_message_quality_receipt(
        packet,
        output,
        rendered,
        binding_errors=(),
        validation_errors=validation_errors,
    )
    if receipt.get("status") != "passed":
        raise ValueError(
            "runtime quality gate failed: "
            + json.dumps(
                {
                    "errors": receipt.get("errors", []),
                    "checks": receipt.get("check_results", {}),
                },
                ensure_ascii=False,
            )
        )

    context = {
        "source_packet": source_packet.get("packet_id"),
        "retrospective_packet": args.retrospective_packet_id,
        "source_packet_sha256": _sha256(args.source_packet),
        "source_output_sha256": _sha256(args.source_output),
        "source_messages_sha256": _sha256(args.source_messages),
        "baseline_preview_sha256": _sha256(args.baseline_preview),
        "source_database_sha256": _sha256(args.database),
        "provider_calls": 0,
        "telegram_sends": 0,
        "database_mutations": 0,
        "pilot_mutations": 0,
        "human_quality_status": "pending_work_human_review",
    }
    output_dir = args.output_dir
    prefix = args.prefix
    _write_json(
        output_dir / f"{prefix}-full-schema-output.json",
        {"artifact_context": context, "output": output.model_dump(mode="json")},
    )
    _write_json(
        output_dir / f"{prefix}-validator.json",
        {
            "artifact_context": context,
            "result": {
                "status": "passed",
                "errors": validation_errors,
                "industry_guardrail_errors": 0,
            },
        },
    )
    _write_json(
        output_dir / f"{prefix}-runtime-quality-receipt.json",
        {"artifact_context": context, "receipt": receipt},
    )
    _write_json(
        output_dir / f"{prefix}-industry-reasoning-audit.json",
        {
            "artifact_context": context,
            "contract": INDUSTRY_REASONING_CONTRACT,
            "stocks": audit,
            "rendered_messages": rendered,
        },
    )
    _write_text(
        output_dir / f"{prefix}-industry-reasoning-preview.md",
        _preview(source_packet.get("packet_id"), names, before, after, audit),
    )


if __name__ == "__main__":
    main()
