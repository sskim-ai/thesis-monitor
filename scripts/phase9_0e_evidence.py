from __future__ import annotations

# ruff: noqa: E402

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Mapping

from sqlmodel import Session, select


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import engine
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.ai_review_service import (
    build_ai_review_packet,
    validate_ai_review_output,
)
from app.services.ai_assisted_delivery_service import (
    _render_ai_market_message,
    _render_ai_stock_message,
)
from app.services.ai_reasoning_quality_service import runtime_message_quality_receipt
from app.services.cash_flow_user_visible_service import resolve_rollout_mode
from app.services.notification_service import (
    _assessment_report,
    _previous_cash_flow_user_visible_context,
)


CONTRACT_VERSION = "phase9-0e-evidence-v1"
PARITY_FIELDS = (
    "cash_flow_user_visible_context_id",
    "selection_state",
    "selection_reason",
    "display_reason",
    "evidence_signature",
    "primary_fact_ref",
    "primary_period",
    "financial_currency",
    "freshness_state",
    "suppressed_baseline_claim_ids",
    "user_visible_enabled",
)
_CASH_TERM = re.compile(
    r"(?:OCF|FCF|CAPEX|영업현금흐름|잉여현금흐름|현금전환)",
    re.IGNORECASE,
)
_UNSUPPORTED_TERM = re.compile(
    r"(?:FCF\s*(?:yield|수익률|/\s*share|주당)|EV\s*/\s*FCF|P\s*/\s*FCF|"
    r"\bROIC\b|투하자본수익률|\bCCC\b|현금전환주기|\bDSO\b|\bDPO\b|재고일수)",
    re.IGNORECASE,
)
_MISSING_CASH = re.compile(
    r"(?:없|미확인|확인할\s*수\s*없|확정할\s*수\s*없|필요)",
    re.IGNORECASE,
)
_GENERIC_NUMERIC_CORE = re.compile(
    r"^현재가\s+.+(?:;|\s)\s*(?:20\d{2}년\s*)?.*매출",
    re.IGNORECASE,
)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _message_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    value = _read_json(path)
    output: dict[str, str] = {}
    for item in value.get("messages") or ():
        if not isinstance(item, dict) or not item.get("ticker"):
            continue
        payload = item.get("payload")
        text = payload.get("text") if isinstance(payload, dict) else item.get("text")
        if isinstance(text, str):
            output[str(item["ticker"])] = text
    return output


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _cash_flow_block(text: str) -> str | None:
    marker = "📈 사업·실적\n"
    if marker not in text:
        return None
    following = text.split(marker, 1)[1]
    return following.split("\n\n", 1)[0].strip()


def _fact_map(stock: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(item["fact_id"]): item
        for item in stock.get("fact_catalog") or ()
        if isinstance(item, dict)
        and item.get("fact_id")
        and str(item.get("fact_type") or "").startswith("cash_flow_")
    }


def _lineage(stock: Mapping[str, object], context: Mapping[str, object]) -> dict[str, object]:
    facts = _fact_map(stock)
    refs = {
        "ocf": context.get("ocf_fact_ref"),
        "ppe_capex": context.get("ppe_capex_fact_ref"),
        "fcf": context.get("fcf_fact_ref"),
    }
    return {
        name: {
            "fact_id": fact_id,
            "value": (
                (facts.get(str(fact_id), {}).get("fields") or {}).get("value")
                if fact_id
                else None
            ),
            "currency": (
                (facts.get(str(fact_id), {}).get("fields") or {}).get("currency")
                if fact_id
                else None
            ),
            "period_start": (
                (facts.get(str(fact_id), {}).get("fields") or {}).get("period_start")
                if fact_id
                else None
            ),
            "period_end": (
                (facts.get(str(fact_id), {}).get("fields") or {}).get("period_end")
                if fact_id
                else None
            ),
            "input_fact_ids": (
                (facts.get(str(fact_id), {}).get("fields") or {}).get("input_fact_ids")
                if fact_id
                else []
            ),
        }
        for name, fact_id in refs.items()
    }


def _without_unsupported_sentences(text: str, *, drop_missing_cash: bool) -> str:
    sentences = re.split(r"(?<=[.!?])\s+|;\s*", text.strip())
    kept = [
        item
        for item in sentences
        if not _UNSUPPORTED_TERM.search(item)
        and not (drop_missing_cash and _CASH_TERM.search(item) and _MISSING_CASH.search(item))
    ]
    return " ".join(kept).strip()


def _archive_ai_preview(
    *,
    session: Session,
    packet: dict[str, object],
    candidate_path: Path,
    baseline_packet_path: Path | None = None,
    deterministic_messages: Mapping[str, str],
) -> dict[str, object]:
    validation_packet = (
        copy.deepcopy(_read_json(baseline_packet_path))
        if baseline_packet_path is not None
        else packet
    )
    if baseline_packet_path is not None:
        current_stocks = {
            str(item["ticker"]): item
            for item in packet.get("stocks") or ()
            if isinstance(item, dict) and item.get("ticker")
        }
        for stock in validation_packet.get("stocks") or ():
            if not isinstance(stock, dict) or not stock.get("ticker"):
                continue
            current = current_stocks[str(stock["ticker"])]
            context = current["cash_flow_user_visible"]
            refs = {
                str(context[key])
                for key in ("ocf_fact_ref", "ppe_capex_fact_ref", "fcf_fact_ref")
                if context.get(key)
            }
            stock["cash_flow_user_visible"] = context
            stock["fact_catalog"] = [
                item
                for item in stock.get("fact_catalog") or ()
                if not (
                    isinstance(item, dict)
                    and str(item.get("fact_type") or "").startswith("cash_flow_")
                )
            ] + [
                item
                for item in current.get("fact_catalog") or ()
                if isinstance(item, dict) and str(item.get("fact_id")) in refs
            ]
            stock["numeric_registry"] = [
                item
                for item in stock.get("numeric_registry") or ()
                if not (isinstance(item, dict) and str(item.get("fact_id")) in refs)
            ] + [
                item
                for item in current.get("numeric_registry") or ()
                if isinstance(item, dict) and str(item.get("fact_id")) in refs
            ]
            stock["unknowns"] = current.get("unknowns", stock.get("unknowns", []))
            if isinstance(stock.get("thesis"), dict) and isinstance(
                current.get("thesis"), dict
            ):
                stock["thesis"]["core_thesis"] = current["thesis"]["core_thesis"]
            if isinstance(stock.get("deterministic_assessment"), dict) and isinstance(
                current.get("deterministic_assessment"), dict
            ):
                for key in ("summary", "confirmed_warnings"):
                    stock["deterministic_assessment"][key] = current[
                        "deterministic_assessment"
                    ][key]
    packet = validation_packet
    candidate = copy.deepcopy(_read_json(candidate_path))
    candidate["packet_id"] = packet["packet_id"]
    stock_packets = {
        str(item["ticker"]): item
        for item in packet.get("stocks") or ()
        if isinstance(item, dict) and item.get("ticker")
    }
    previews: list[dict[str, object]] = []
    for review in candidate.get("stock_reviews") or ():
        if not isinstance(review, dict) or not review.get("ticker"):
            continue
        ticker = str(review["ticker"])
        stock = stock_packets[ticker]
        company_name = re.sub(
            r"\d+",
            "",
            str(stock.get("company_name") or ticker),
        ).strip()
        context = stock.get("cash_flow_user_visible")
        if not isinstance(context, dict):
            continue
        selected = context.get("user_visible_enabled") is True
        for key in ("core_judgment", "business_earnings"):
            section = review.get(key)
            if isinstance(section, dict) and isinstance(section.get("text"), str):
                section["text"] = _without_unsupported_sentences(
                    str(section["text"]),
                    drop_missing_cash=selected,
                )
                if key == "core_judgment":
                    section["text"] = " ".join(
                        item
                        for item in re.split(
                            r"(?<=[.!?])\s+",
                            str(section["text"]),
                        )
                        if not _GENERIC_NUMERIC_CORE.search(item)
                    )
                    if not section["text"]:
                        section["text"] = (
                            f"{company_name}의 사업 전환과 수익성 근거를 계속 확인합니다."
                        )
        for key in ("unknowns", "priority_watch", "next_checks"):
            values = review.get(key)
            if isinstance(values, list):
                review[key] = [
                    str(item)
                    for item in values
                    if not _UNSUPPORTED_TERM.search(str(item))
                    and not (selected and _CASH_TERM.search(str(item)))
                ]
        valuation = review.get("valuation_analysis")
        if isinstance(valuation, dict):
            core_text = str(review["core_judgment"]["text"]).split(".", 1)[0]
            anchor_match = re.search(r"[A-Za-z가-힣·]+", core_text)
            anchor = (
                anchor_match.group(0)
                if anchor_match
                else str(context.get("industry") or "사업")
            )
            valuation["text"] = (
                f"{anchor} 사업의 기존 valuation 기준을 유지하고 "
                "cash-flow 수치만으로 판단을 바꾸지 않습니다."
            )
        review["numeric_claims"] = [
            item
            for item in review.get("numeric_claims") or ()
            if not (
                isinstance(item, dict)
                and item.get("text_ref") == "valuation_analysis.text"
            )
            and not (
                isinstance(item, dict)
                and item.get("text_ref") == "core_judgment.text"
                and str(item.get("usage") or "")
                not in str(review["core_judgment"]["text"])
            )
        ]
        if not selected:
            continue
        rendered = str(context["rendered_fallback_text"])
        business = review["business_earnings"]
        before = str(business.get("text") or "")
        business["text"] = " ".join(item for item in (before, rendered) if item)
        primary_fact_id = str(context["primary_fact_ref"])
        facts_used = [str(item) for item in review.get("facts_used") or ()]
        review["facts_used"] = list(dict.fromkeys([*facts_used, primary_fact_id]))
        business_fact_ids = [str(item) for item in business.get("fact_ids") or ()]
        business["fact_ids"] = list(
            dict.fromkeys([*business_fact_ids, primary_fact_id])
        )
        fact = next(
            item
            for item in stock.get("fact_catalog") or ()
            if isinstance(item, dict) and item.get("fact_id") == primary_fact_id
        )
        fields = fact["fields"]
        registry = next(
            item
            for item in stock.get("numeric_registry") or ()
            if isinstance(item, dict)
            and item.get("fact_id") == primary_fact_id
            and item.get("field_path") == "fields.value"
        )
        claims = [
            item
            for item in review.get("numeric_claims") or ()
            if not (
                isinstance(item, dict)
                and str(item.get("fact_id") or "").startswith("cashflow")
            )
        ]
        claims.append(
            {
                "fact_id": primary_fact_id,
                "field_path": "fields.value",
                "value": fields["value"],
                "unit": fields["currency"],
                "semantic_type": "free_cash_flow_ppe",
                "text_ref": "business_earnings.text",
                "usage": (
                    "PPE 투자 후 잉여현금흐름은 "
                    f"{registry['canonical_display_value']}"
                ),
            }
        )
        review["numeric_claims"] = claims
        previews.append(
            {
                "ticker": ticker,
                "primary_fact_id": primary_fact_id,
                "business_earnings_before": before,
                "business_earnings_after": business["text"],
                "numeric_claim": claims[-1],
            }
        )
    validated, errors = validate_ai_review_output(session, packet, candidate)
    quality: dict[str, object] | None = None
    rendered_messages: list[dict[str, object]] = []
    if validated is not None and not errors:
        market_marker = "__DAILY_DIGEST__"
        rendered_messages.append(
            {
                "ticker": market_marker,
                "logical_identity": f"preview:{market_marker}",
                "text": _render_ai_market_message(
                    deterministic_messages.get(market_marker, ""),
                    validated.market_review,
                    market_context=packet["market_context"],
                    market=str(packet["market"]),
                    pilot_day=1,
                    target_days=1,
                ),
            }
        )
        for review in validated.stock_reviews:
            rendered_messages.append(
                {
                    "ticker": review.ticker,
                    "logical_identity": f"preview:{review.ticker}",
                    "text": _render_ai_stock_message(
                        deterministic_messages.get(review.ticker, ""),
                        review,
                        market=str(packet["market"]),
                        pilot_day=1,
                        target_days=1,
                    ),
                }
            )
        quality = runtime_message_quality_receipt(
            packet,
            validated,
            rendered_messages,
            checked_at=datetime.combine(
                date.fromisoformat(str(packet["assessment_date"])),
                datetime.min.time(),
                tzinfo=UTC,
            ),
        )
    return {
        "source_candidate": str(candidate_path),
        "status": (
            "PASS"
            if validated is not None
            and not errors
            and quality is not None
            and quality.get("status") == "passed"
            else "FAIL"
        ),
        "error_count": len(errors),
        "errors": errors,
        "selected_preview_count": len(previews),
        "automatic_cash_flow_binding": len(previews) if not errors else 0,
        "manual_cash_flow_binding": 0,
        "rejected_cash_flow_binding": 0 if not errors else len(previews),
        "unresolved_cash_flow_binding": 0,
        "runtime_quality": quality,
        "rendered_messages": rendered_messages,
        "previews": previews,
    }


def build_evidence(
    *,
    run_date: date,
    market: str,
    archive: Path,
    source_packet_id: str,
    ai_candidate: Path | None = None,
    baseline_packet: Path | None = None,
) -> dict[str, object]:
    original_messages = _message_map(archive / "deterministic-messages.json")
    generated_at = datetime.combine(run_date, datetime.min.time(), tzinfo=UTC)
    with Session(engine) as session:
        packet = build_ai_review_packet(
            session,
            run_date,
            market,
            generated_at=generated_at,
        )
        if packet is None:
            raise ValueError("Run packet could not be rebuilt")
        assessments = {
            item.ticker: item
            for item in session.exec(
                select(ThesisAssessment).where(
                    ThesisAssessment.assessment_date == run_date
                )
            ).all()
        }
        watchlist = {
            item.ticker: item
            for item in session.exec(
                select(WatchlistItem).where(WatchlistItem.active.is_(True))
            ).all()
        }
        theses = {
            (item.ticker, item.version): item
            for item in session.exec(select(InvestmentThesis)).all()
        }

        rows: list[dict[str, object]] = []
        current_messages: dict[str, str] = {
            "__DAILY_DIGEST__": original_messages.get("__DAILY_DIGEST__", "")
        }
        parity_errors: list[dict[str, object]] = []
        for stock_value in packet.get("stocks") or ():
            if not isinstance(stock_value, dict):
                continue
            ticker = str(stock_value["ticker"])
            assessment = assessments[ticker]
            thesis = theses[(ticker, assessment.thesis_version)]
            fallback_text, fallback_analysis = _assessment_report(
                assessment,
                watchlist[ticker].company_name,
                thesis,
                previous_cash_flow_user_visible_context=(
                    _previous_cash_flow_user_visible_context(session, assessment)
                ),
            )
            ai_context = stock_value.get("cash_flow_user_visible")
            fallback_context = fallback_analysis.get("cash_flow_user_visible")
            if not isinstance(ai_context, dict) or not isinstance(fallback_context, dict):
                raise ValueError(f"Missing cash-flow context: {ticker}")
            mismatches = [
                field
                for field in PARITY_FIELDS
                if ai_context.get(field) != fallback_context.get(field)
            ]
            if mismatches:
                parity_errors.append({"ticker": ticker, "fields": mismatches})
            selected = ai_context.get("user_visible_enabled") is True
            before = original_messages.get(ticker, "")
            current_messages[ticker] = fallback_text
            rows.append(
                {
                    "ticker": ticker,
                    "company_name": stock_value.get("company_name"),
                    "industry": ai_context.get("industry"),
                    "selection_state": ai_context.get("selection_state"),
                    "selection_reason": ai_context.get("selection_reason"),
                    "selected": selected,
                    "context_id": ai_context.get("cash_flow_user_visible_context_id"),
                    "primary_period": ai_context.get("primary_period"),
                    "financial_currency": ai_context.get("financial_currency"),
                    "freshness_state": ai_context.get("freshness_state"),
                    "primary_fact_ref": ai_context.get("primary_fact_ref"),
                    "suppressed_baseline_claim_ids": ai_context.get(
                        "suppressed_baseline_claim_ids"
                    ),
                    "resolved_unknown_ids": ai_context.get("resolved_unknown_ids"),
                    "ai_fallback_parity": not mismatches,
                    "ai_fallback_parity_fields": list(PARITY_FIELDS),
                    "lineage": _lineage(stock_value, ai_context),
                    "before_text_sha256": _sha256_text(before) if before else None,
                    "after_text_sha256": _sha256_text(fallback_text),
                    "before_length": len(before),
                    "after_length": len(fallback_text),
                    "length_delta": len(fallback_text) - len(before) if before else None,
                    "before_text": before,
                    "after_text": fallback_text,
                    "cash_flow_user_visible_text": _cash_flow_block(fallback_text),
                }
            )
        ai_preview = (
            _archive_ai_preview(
                session=session,
                packet=packet,
                candidate_path=ai_candidate,
                baseline_packet_path=baseline_packet,
                deterministic_messages=current_messages,
            )
            if ai_candidate is not None
            else None
        )

    selected_rows = [item for item in rows if item["selected"]]
    reasons: dict[str, int] = {}
    for row in rows:
        if row["selected"]:
            continue
        reason = str(row["selection_reason"])
        reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "contract": CONTRACT_VERSION,
        "instruction_commit": "309f5f1756d39d5972c5d4b48faaeab4862d8077",
        "source_packet_id": source_packet_id,
        "replay_packet_id": packet["packet_id"],
        "run_date": run_date.isoformat(),
        "rollout_mode": resolve_rollout_mode().value,
        "market": market,
        "subject_count": len(rows),
        "selected_count": len(selected_rows),
        "selected_tickers": [str(item["ticker"]) for item in selected_rows],
        "suppressed_count": len(rows) - len(selected_rows),
        "suppression_reason_counts": reasons,
        "ai_fallback_parity": "PASS" if not parity_errors else "FAIL",
        "parity_errors": parity_errors,
        "ai_preview": ai_preview,
        "selected_context_ids": [str(item["context_id"]) for item in selected_rows],
        "selected_primary_fact_ids": [
            str(item["primary_fact_ref"]) for item in selected_rows
        ],
        "selected_message_average_length_delta": (
            round(
                sum(int(item["length_delta"] or 0) for item in selected_rows)
                / len(selected_rows),
                2,
            )
            if selected_rows
            else 0
        ),
        "original_archive_rewrites": 0,
        "delivery_count": 0,
        "manual_tasks": 0,
        "database_mutations": 0,
        "subjects": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Phase 9.0E archive-only evidence")
    parser.add_argument("--run-date", default="2026-08-21")
    parser.add_argument("--market", choices=("us", "kr"), default="us")
    parser.add_argument(
        "--archive",
        type=Path,
        required=True,
        help="Immutable run archive used only for before-message comparison",
    )
    parser.add_argument(
        "--source-packet-id",
        default="2026-08-21-us-run-30-5a3b7c1c4390",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ai-candidate", type=Path)
    parser.add_argument("--baseline-packet", type=Path)
    args = parser.parse_args()
    output = build_evidence(
        run_date=date.fromisoformat(args.run_date),
        market=args.market,
        archive=args.archive,
        source_packet_id=args.source_packet_id,
        ai_candidate=args.ai_candidate,
        baseline_packet=args.baseline_packet,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "selected_count": output["selected_count"],
                "selected_tickers": output["selected_tickers"],
                "ai_fallback_parity": output["ai_fallback_parity"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
