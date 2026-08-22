from __future__ import annotations

import argparse
import copy
import json
from datetime import UTC, date, datetime
from pathlib import Path

from sqlmodel import Session

from app.database import engine
from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_assisted_delivery_service import (
    _render_ai_market_message,
    _render_ai_stock_message,
)
from app.services.ai_reasoning_quality_service import runtime_message_quality_receipt
from app.services.ai_review_service import validate_ai_review_output
from app.services.cash_flow_capital_efficiency_service import PeriodIdentity, PeriodType
from app.services.cash_flow_user_visible_service import (
    cash_flow_period_claim_contract,
)
from app.services.runtime_specificity_service import build_runtime_specificity_plan


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _period_contract(context: dict[str, object]) -> dict[str, object] | None:
    value = context.get("primary_period")
    if not isinstance(value, dict):
        return None
    try:
        period = PeriodIdentity(
            start=date.fromisoformat(str(value["period_start"])),
            end=date.fromisoformat(str(value["period_end"])),
            period_type=PeriodType(str(value["period_type"])),
            fiscal_year=int(value["fiscal_year"]),
            fiscal_quarter=(
                int(value["fiscal_quarter"])
                if value.get("fiscal_quarter") is not None
                else None
            ),
        )
    except (KeyError, TypeError, ValueError):
        return None
    return cash_flow_period_claim_contract(period)


def enrich_packet(packet: dict[str, object]) -> dict[str, object]:
    enriched = copy.deepcopy(packet)
    for stock in enriched.get("stocks", []):
        if not isinstance(stock, dict):
            continue
        context = stock.get("cash_flow_user_visible")
        if isinstance(context, dict):
            contract = _period_contract(context)
            if contract:
                context.update(
                    {
                        "period_identity_contract": contract["contract"],
                        "required_period_label": contract["required_period_label"],
                        "duration_basis": contract["duration_basis"],
                        "is_ytd": contract["is_ytd"],
                        "is_fy": contract["is_fy"],
                        "allowed_period_claims": contract["allowed_period_claims"],
                        "forbidden_period_claims": contract[
                            "forbidden_period_claims"
                        ],
                        "fcf_scope": (
                            "OCF - PPE CAPEX"
                            if context.get("primary_fact_ref")
                            else None
                        ),
                    }
                )
                primary = context.get("primary_period")
                if isinstance(primary, dict):
                    primary.update(
                        {
                            "canonical_label": contract["required_period_label"],
                            "duration_basis": contract["duration_basis"],
                            "is_ytd": contract["is_ytd"],
                            "is_fy": contract["is_fy"],
                        }
                    )
        stock["runtime_specificity_plan"] = build_runtime_specificity_plan(stock)
    return enriched


def repaired_candidate(
    packet: dict[str, object],
    candidate: dict[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    repaired = copy.deepcopy(candidate)
    stocks = {
        str(item.get("ticker")): item
        for item in packet.get("stocks", [])
        if isinstance(item, dict)
    }
    changes: list[dict[str, object]] = []

    def fold_numeric_sentence(review: dict[str, object], section_name: str) -> bool:
        section = review.get(section_name)
        if not isinstance(section, dict):
            return False
        text_ref = f"{section_name}.text"
        usages = [
            f"{{{{numeric:{item['ref_id']}}}}}"
            for item in review.get("numeric_fact_refs", [])
            if isinstance(item, dict)
            and item.get("text_ref") == text_ref
            and item.get("ref_id")
        ]
        if len(usages) < 2:
            return False
        sequence = "; ".join(usages)
        text = str(section.get("text") or "")
        standalone = f"{sequence}."
        changed = False
        if text.endswith(standalone):
            base = text[: -len(standalone)].rstrip(" .")
            section["text"] = f"{base}: {sequence}."
            changed = True
        elif text.startswith(standalone):
            tail = text[len(standalone) :].strip()
            if not tail:
                return False
            first, separator, rest = tail.partition(".")
            section["text"] = (
                f"{first.rstrip()}: {sequence}."
                + (f" {rest.lstrip()}" if separator and rest.strip() else "")
            )
            changed = True
        if changed and section_name == "valuation_analysis":
            for item in review.get("valuation_interpretation_refs", []):
                if isinstance(item, dict) and item.get("text_ref") == text_ref:
                    item["exact_text_span"] = section["text"]
        return changed

    for review in repaired.get("stock_reviews", []):
        if not isinstance(review, dict):
            continue
        ticker = str(review.get("ticker") or "")
        stock = stocks.get(ticker, {})
        context = stock.get("cash_flow_user_visible")
        label = (
            str(context.get("required_period_label") or "")
            if isinstance(context, dict)
            else ""
        )
        business = review.get("business_earnings")
        fallback_text = (
            str(context.get("rendered_fallback_text") or "")
            if isinstance(context, dict)
            else ""
        )
        cash_ref = next(
            (
                str(item.get("ref_id"))
                for item in review.get("numeric_fact_refs", [])
                if isinstance(item, dict)
                and item.get("text_ref") == "business_earnings.text"
                and item.get("fact_id") == context.get("primary_fact_ref")
            ),
            None,
        ) if isinstance(context, dict) else None
        if label and isinstance(business, dict) and fallback_text and cash_ref:
            placeholder = f"{{{{numeric:{cash_ref}}}}}"
            subject = fallback_text.split("PPE 투자 후", 1)[0].rstrip()
            if subject.endswith("의"):
                subject = subject[:-1]
            original = str(business.get("text") or "")
            business["text"] = original.replace(
                placeholder,
                f"{subject} 기준 {placeholder}",
                1,
            )
            changes.append(
                {
                    "ticker": ticker,
                    "change": "canonical_period_and_industry_cash_flow_seed",
                }
            )
        valid_ids = {
            str(item.get("fact_id"))
            for item in stock.get("fact_catalog", [])
            if isinstance(item, dict) and item.get("fact_id")
        }
        for section_name in (
            "core_judgment",
            "business_earnings",
            "price_positioning",
            "supply_analysis",
            "valuation_analysis",
        ):
            section = review.get(section_name)
            if not isinstance(section, dict):
                continue
            declared = [str(item) for item in section.get("fact_ids", [])]
            allowed = [item for item in declared if item in valid_ids]
            removed = [item for item in declared if item not in valid_ids]
            if removed:
                section["fact_ids"] = allowed
                changes.append(
                    {
                        "ticker": ticker,
                        "change": "remove_unavailable_price_fact_id",
                        "section": section_name,
                        "fact_ids": removed,
                    }
                )
        for section_name in ("core_judgment", "valuation_analysis"):
            if fold_numeric_sentence(review, section_name):
                changes.append(
                    {
                        "ticker": ticker,
                        "change": "fold_numeric_evidence_into_decision_sentence",
                        "section": section_name,
                    }
                )
    return repaired, changes


def _rendered_messages(
    packet: dict[str, object],
    output: AIDailyReviewOutput,
    deterministic: dict[str, object],
) -> list[dict[str, object]]:
    source = {
        str(item.get("ticker")): str(
            (item.get("payload") or {}).get("text") or ""
        )
        for item in deterministic.get("messages", [])
        if isinstance(item, dict) and isinstance(item.get("payload"), dict)
    }
    messages = [
        {
            "ticker": "__DAILY_DIGEST__",
            "logical_identity": "market:us",
            "text": _render_ai_market_message(
                source.get("__DAILY_DIGEST__", ""),
                output.market_review,
                market_context=dict(packet.get("market_context") or {}),
                market="us",
                pilot_day=1,
                target_days=1,
            ),
        }
    ]
    messages.extend(
        {
            "ticker": review.ticker,
            "logical_identity": f"stock:{review.ticker}",
            "text": _render_ai_stock_message(
                source.get(review.ticker, f"🏢 {review.ticker}"),
                review,
                market="us",
                pilot_day=1,
                target_days=1,
            ),
        }
        for review in output.stock_reviews
    )
    return messages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--deterministic-messages", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()

    packet = dict(_read(args.packet))
    candidate = dict(_read(args.candidate))
    deterministic = dict(_read(args.deterministic_messages))
    enriched = enrich_packet(packet)
    repaired, changes = repaired_candidate(enriched, candidate)
    with Session(engine) as session:
        original_output, original_errors = validate_ai_review_output(
            session, packet, candidate
        )
        repaired_output, repaired_errors = validate_ai_review_output(
            session, enriched, repaired
        )
    messages = (
        _rendered_messages(enriched, repaired_output, deterministic)
        if repaired_output is not None
        else []
    )
    quality = (
        runtime_message_quality_receipt(
            enriched,
            repaired_output,
            messages,
            validation_errors=repaired_errors,
            checked_at=datetime(2026, 8, 22, tzinfo=UTC),
        )
        if repaired_output is not None
        else None
    )
    summary = {
        "packet_id": packet.get("packet_id"),
        "original_candidate_schema_valid": original_output is not None,
        "original_error_count": len(original_errors),
        "original_errors": original_errors,
        "repaired_candidate_schema_valid": repaired_output is not None,
        "repaired_error_count": len(repaired_errors),
        "repaired_errors": repaired_errors,
        "changes": changes,
        "numeric_claims_unchanged": (
            candidate.get("stock_reviews") is not None
            and [
                item.get("numeric_claims")
                for item in candidate.get("stock_reviews", [])
            ]
            == [
                item.get("numeric_claims")
                for item in repaired.get("stock_reviews", [])
            ]
        ),
        "quality_status": quality.get("status") if quality else "not_run",
        "quality_errors": quality.get("errors") if quality else [],
        "quality_checks": quality.get("check_results") if quality else {},
        "message_count": len(messages),
        "archive_rewrite": 0,
        "production_delivery": 0,
    }
    _write(args.output_directory / "run32-repaired-candidate.json", repaired)
    _write(args.output_directory / "run32-replay-result.json", summary)
    if quality is not None:
        _write(args.output_directory / "run32-runtime-quality-receipt.json", quality)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
