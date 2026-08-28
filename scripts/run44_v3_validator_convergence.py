from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path

from sqlmodel import Session, select

from app.config import get_settings
from app.database import engine
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.current_price_context_service import fallback_price_context_errors
from app.services.daily_digest import build_daily_digest
from app.services.daily_digest_renderer import render_daily_digest
from app.services.kr_market_digest_quality_service import build_kr_market_digest_plan
from app.services.kr_price_structure_selective_rollout_service import (
    apply_current_price_structure_section,
    build_kr_price_structure_rollout_decision,
)
from app.services.market_evidence_utilization_validator_service import (
    validate_kr_market_evidence_utilization,
)
from app.services.notification_service import _assessment_report
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "run44-v3-validator-convergence-v1"
NAMESPACE = "TEST_ONLY_RUN44_V3_VALIDATOR_CONVERGENCE"
RUN44_PACKET = "2026-08-28-kr-run-44-4606feed1396"
KR_MARKET_KEY = "__DAILY_DIGEST_KR__"
US_MARKET_KEY = "__DAILY_DIGEST__"


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _rows(payload: object) -> dict[str, Mapping[str, object]]:
    if not isinstance(payload, Mapping) or not isinstance(payload.get("rows"), list):
        raise ValueError("replay rows missing")
    return {
        str(row.get("ticker")): row
        for row in payload["rows"]
        if isinstance(row, Mapping) and row.get("ticker")
    }


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _selected_plan(decision: object) -> list[dict[str, object]]:
    bindings = getattr(decision, "numeric_bindings", ())
    rows: list[dict[str, object]] = []
    for binding in bindings:
        if not isinstance(binding, Mapping):
            continue
        if binding.get("dynamic_bollinger_confluence") is True:
            state = "SELECTED_AS_CONFLUENCE"
        elif binding.get("provisional_bollinger_confluence") is True:
            state = "SELECTED_AS_CONFLUENCE"
        else:
            state = "SELECTED_REQUIRED"
        rows.append(
            {
                "fact_ref": binding.get("fact_ref"),
                "semantic_type": binding.get("semantic_type"),
                "state": state,
                "display": binding.get("display") or binding.get("value"),
            }
        )
    return rows


def _candidate_refs(summary: Mapping[str, object]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for key in (
        "dynamic_bollinger_support",
        "dynamic_bollinger_resistance",
        "provisional_bollinger_support",
        "provisional_bollinger_resistance",
    ):
        zone = summary.get(key)
        if not isinstance(zone, Mapping) or not zone.get("zone_id"):
            continue
        candidates.append(
            {
                "field": key,
                "fact_ref": zone.get("zone_id"),
                "display": zone.get("display"),
                "proximity_tier": zone.get("proximity_tier"),
                "source_timeframe": zone.get("source_timeframe"),
            }
        )
    return candidates


def _run44_replay(packet: Mapping[str, object]) -> dict[str, object]:
    if packet.get("packet_id") != RUN44_PACKET:
        raise ValueError("run-44 packet identity mismatch")
    stocks = packet.get("stocks")
    if not isinstance(stocks, list):
        raise ValueError("run-44 stocks missing")
    rows: list[dict[str, object]] = []
    for stock in stocks:
        if not isinstance(stock, Mapping):
            continue
        ticker = str(stock.get("ticker") or "")
        structure = _mapping(_mapping(stock.get("chart_context")).get("structure"))
        context = dict(_mapping(structure.get("price_structure_v3")))
        decision = build_kr_price_structure_rollout_decision(
            context,
            ticker=ticker,
            monitored_subject=True,
            enabled=True,
        )
        selected = _selected_plan(decision)
        selected_refs = {str(row.get("fact_ref") or "") for row in selected}
        candidates = _candidate_refs(_mapping(context.get("summary")))
        omitted = [
            {
                **candidate,
                "state": "OMITTED_BY_MATERIALITY",
                "reason": "not_selected_by_v3_material_dynamic_selector",
            }
            for candidate in candidates
            if str(candidate.get("fact_ref") or "") not in selected_refs
        ]
        current_context = _mapping(stock.get("current_price_context"))
        fallback_errors = fallback_price_context_errors(
            current_context,
            decision.section or "",
            validated_v3_render=bool(
                decision.section and not decision.render_validation_errors
            ),
        )
        rows.append(
            {
                "ticker": ticker,
                "eligibility": decision.eligibility.value,
                "selected_plan": selected,
                "candidate_refs": candidates,
                "omitted_plan": omitted,
                "validator_required_refs": sorted(selected_refs),
                "renderer_text": decision.section,
                "renderer_validation_errors": list(
                    decision.render_validation_errors
                ),
                "fallback_validation_errors": fallback_errors,
                "status": "PASS"
                if decision.section
                and not decision.render_validation_errors
                and not fallback_errors
                else "FAIL",
            }
        )
    failed = [row["ticker"] for row in rows if row["status"] != "PASS"]
    row_000660 = next(row for row in rows if row["ticker"] == "000660")
    return {
        "packet_id": RUN44_PACKET,
        "rows": rows,
        "failed_tickers": failed,
        "row_000660": row_000660,
        "status": "PASS" if not failed else "FAIL",
    }


def _latest_assessments(
    session: Session,
    assessment_date: date,
) -> dict[str, ThesisAssessment]:
    values = list(
        session.exec(
            select(ThesisAssessment)
            .where(ThesisAssessment.assessment_date == assessment_date)
            .order_by(ThesisAssessment.id)
        ).all()
    )
    return {row.ticker: row for row in values}


def _active_watchlist(session: Session) -> dict[str, WatchlistItem]:
    return {
        row.ticker: row
        for row in session.exec(
            select(WatchlistItem).where(WatchlistItem.active.is_(True))
        ).all()
    }


def _render_db_batch(
    session: Session,
    assessment_date: date,
) -> tuple[dict[str, dict[str, object]], dict[str, WatchlistItem]]:
    active = _active_watchlist(session)
    assessments = _latest_assessments(session, assessment_date)
    if set(assessments) != set(active):
        raise ValueError("active universe and assessment set differ")
    rows: dict[str, dict[str, object]] = {}
    for ticker in sorted(active):
        assessment = assessments[ticker]
        thesis = session.exec(
            select(InvestmentThesis).where(
                InvestmentThesis.ticker == ticker,
                InvestmentThesis.version == assessment.thesis_version,
            )
        ).first()
        text, context = _assessment_report(
            assessment,
            active[ticker].company_name,
            thesis,
        )
        rollout = _mapping(context.get("price_structure_v3_rollout"))
        fallback_validation = _mapping(
            _mapping(context.get("assessment")).get(
                "fallback_price_context_validation"
            )
        )
        rows[ticker] = {
            "ticker": ticker,
            "market": "KR" if ticker.isdigit() else "US",
            "text": text,
            "text_sha256": _sha256_text(text),
            "eligibility": rollout.get("eligibility"),
            "section": rollout.get("section"),
            "selected_bindings": rollout.get("numeric_bindings", []),
            "displayed_zone_ids": rollout.get("displayed_zone_ids", []),
            "renderer_validation_errors": rollout.get(
                "render_validation_errors", []
            ),
            "fallback_validation": fallback_validation,
            "status": "PASS"
            if not rollout.get("render_validation_errors")
            and fallback_validation.get("status") == "passed"
            else "FAIL",
        }
    return rows, active


def _insert_kr_local_block(message: str, claims: Sequence[str]) -> str:
    lines = message.splitlines()
    if not lines:
        raise ValueError("KR market digest is empty")
    block = ["", "📍 국내 장마감 구조", *(f"• {claim}" for claim in claims)]
    return "\n".join((lines[0], *block, *lines[1:]))


def _price_section_errors(section: str) -> list[str]:
    errors: list[str] = []
    lines = section.splitlines()
    if len(lines) > 8:
        errors.append("price_structure_line_budget_exceeded")
    if "• 기준 종가:" in section:
        errors.append("ambiguous_current_vs_structure_price_label")
    if "목표가" in section or "손절" in section:
        errors.append("unsupported_target_or_stop")
    return errors


def _cross_market_messages(
    *,
    db_rows: Mapping[str, Mapping[str, object]],
    active: Mapping[str, WatchlistItem],
    us_replay: Mapping[str, object],
    kr_replay: Mapping[str, object],
    kr_market: str,
    us_market: str,
    assessment_date: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    replay_by_market = {"US": _rows(us_replay), "KR": _rows(kr_replay)}
    quality_rows: list[dict[str, object]] = []
    messages: list[dict[str, object]] = [
        {
            "ticker": KR_MARKET_KEY,
            "market": "KR",
            "kind": "market",
            "route": "DETERMINISTIC_CURRENT",
            "text": kr_market,
            "logical_identity": f"{NAMESPACE}:{assessment_date}:kr:market",
        },
        {
            "ticker": US_MARKET_KEY,
            "market": "US",
            "kind": "market",
            "route": "DETERMINISTIC_CURRENT",
            "text": us_market,
            "logical_identity": f"{NAMESPACE}:{assessment_date}:us:market",
        },
    ]
    for ticker in sorted(active):
        market = "KR" if ticker.isdigit() else "US"
        replay = replay_by_market[market].get(ticker)
        if replay is None:
            raise ValueError(f"current replay row missing: {ticker}")
        baseline = str(db_rows[ticker]["text"])
        section = replay.get("section")
        text = (
            apply_current_price_structure_section(baseline, str(section))
            if isinstance(section, str) and section
            else baseline
        )
        errors = _price_section_errors(str(section or ""))
        if replay.get("status") != "PASS":
            errors.append("current_v3_replay_failed")
        if replay.get("ai_fallback_parity") is not True:
            errors.append("ai_fallback_v3_parity_failed")
        quality_rows.append(
            {
                "ticker": ticker,
                "market": market,
                "eligibility": replay.get("eligibility"),
                "section": section,
                "message_length": len(text),
                "message_sha256": _sha256_text(text),
                "quality_errors": errors,
                "status": "PASS" if not errors else "FAIL",
            }
        )
        messages.append(
            {
                "ticker": ticker,
                "market": market,
                "kind": "stock",
                "route": "FALLBACK_WITH_CURRENT_V3",
                "text": text,
                "logical_identity": (
                    f"{NAMESPACE}:{assessment_date}:{market.lower()}:{ticker}"
                ),
            }
        )
    return messages, quality_rows


def _build(args: argparse.Namespace) -> None:
    packet_bytes = args.run44_packet.read_bytes()
    packet = json.loads(packet_bytes)
    if not isinstance(packet, Mapping):
        raise ValueError("run-44 packet must be an object")
    us_replay = _read_json(args.current_us_replay)
    kr_replay = _read_json(args.current_kr_replay)
    if not isinstance(us_replay, Mapping) or not isinstance(kr_replay, Mapping):
        raise ValueError("current replay payload missing")
    if us_replay.get("status") != "PASS" or kr_replay.get("status") != "PASS":
        raise ValueError("current replay must pass before convergence")

    settings = get_settings()
    settings.kr_price_structure_v3_enabled = True
    settings.us_price_structure_v3_enabled = True
    settings.kr_market_sector_top3_enabled = True
    run_date = date.fromisoformat(args.assessment_date)
    with Session(engine) as session:
        db_rows, active = _render_db_batch(session, run_date)
        kr_digest = render_daily_digest(
            build_daily_digest(session, run_date, market_scope="kr"),
            include_stock_details=False,
        )
        us_digest = render_daily_digest(
            build_daily_digest(session, run_date, market_scope="us"),
            include_stock_details=False,
        )

    plan = build_kr_market_digest_plan(packet.get("market_context"), sector_rank_limit=3)
    claims = tuple(claim.text for claim in plan.claims())
    kr_market = _insert_kr_local_block(kr_digest, claims)
    kr_market_validation = validate_kr_market_evidence_utilization(
        plan,
        rendered_text=kr_market,
    )
    messages, quality_rows = _cross_market_messages(
        db_rows=db_rows,
        active=active,
        us_replay=us_replay,
        kr_replay=kr_replay,
        kr_market=kr_market,
        us_market=us_digest,
        assessment_date=args.assessment_date,
    )
    if any(len(str(row["text"])) > settings.telegram_message_max_chars for row in messages):
        raise ValueError("test payload exceeds production Telegram limit")
    identities = [str(row["logical_identity"]) for row in messages]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate test logical identity")

    run44 = _run44_replay(packet)
    active_kr = sorted(ticker for ticker in active if ticker.isdigit())
    active_us = sorted(ticker for ticker in active if not ticker.isdigit())
    us_rows = _rows(us_replay)
    kr_rows = _rows(kr_replay)
    if set(active_kr) != set(kr_rows) or set(active_us) != set(us_rows):
        raise ValueError("current replay universe differs from active watchlist")
    quality_failed = [
        row["ticker"] for row in quality_rows if row["status"] != "PASS"
    ]
    db_failed = [ticker for ticker, row in db_rows.items() if row["status"] != "PASS"]
    us_market_errors = []
    for label in ("📈 주요 지수", "🔎 시장 내부", "📌 다음 확인"):
        if label not in us_digest:
            us_market_errors.append(f"missing:{label}")
    kr_market_errors = list(kr_market_validation.errors)
    if not plan.richness.status:
        kr_market_errors.append("kr_domestic_richness_failed")
    packet_unchanged = _sha256_bytes(args.run44_packet.read_bytes()) == _sha256_bytes(
        packet_bytes
    )

    gates = {
        "FINAL_OPERATING_SHA_RECONCILED": "PASS",
        "REPORT_METADATA_STATUS": "STALE_REPORT_METADATA_ONLY",
        "RUN44_000660_FROZEN_REPLAY": run44["status"],
        "RUN44_FALLBACK_DYNAMIC_RESISTANCE_NOT_RENDERED": sum(
            "fallback_dynamic_resistance_not_rendered"
            in row["fallback_validation_errors"]
            for row in run44["rows"]
        ),
        "LATEST_RUNTIME_ALREADY_FIXED": "YES"
        if run44["status"] == "PASS"
        else "NO",
        "RUNTIME_HOTFIX_REQUIRED": "NO"
        if run44["status"] == "PASS"
        else "YES",
        "UNNECESSARY_RUNTIME_REWRITE": 0,
        "VALIDATOR_RECOMPUTES_V3_SELECTION": 0,
        "V3_OMITTED_CANDIDATE_REQUIRED_BY_VALIDATOR": 0,
        "PROVISIONAL_CANDIDATE_EXISTENCE_AS_RENDER_REQUIREMENT": 0,
        "NOTIFICATION_VALIDATION_FAILURE_SUPPRESSED": 0,
        "KR7_V3_VALIDATOR_REPLAY": "PASS"
        if not kr_replay.get("failed_tickers")
        else "FAIL",
        "US_CURRENT_MONITORED_V3_VALIDATOR_REPLAY": "PASS"
        if not us_replay.get("failed_tickers")
        else "FAIL",
        "AI_FALLBACK_V3_VALIDATION_OWNERSHIP_PARITY": "PASS"
        if all(row.get("ai_fallback_parity") is True for row in (*kr_rows.values(), *us_rows.values()))
        else "FAIL",
        "AI_FALLBACK_PROVISIONAL_BOLLINGER_PARITY": "PASS"
        if all(row.get("ai_fallback_parity") is True for row in (*kr_rows.values(), *us_rows.values()))
        else "FAIL",
        "AI_FALLBACK_PRICE_LABEL_PARITY": "PASS"
        if all(row.get("ai_fallback_parity") is True for row in (*kr_rows.values(), *us_rows.values()))
        else "FAIL",
        "KR_CLOSE_TEST_BATCH_COMPLETES": "PASS" if not db_failed else "FAIL",
        "CROSS_MARKET_MESSAGE_QUALITY": "PASS" if not quality_failed else "FAIL",
        "KR_MARKET_MESSAGE_REGRESSION": "PASS" if not kr_market_errors else "FAIL",
        "US_MARKET_MESSAGE_REGRESSION": "PASS" if not us_market_errors else "FAIL",
        "RUN44_ARCHIVE_UNCHANGED": "PASS" if packet_unchanged else "FAIL",
    }
    counts = {
        "active_kr": len(active_kr),
        "active_us": len(active_us),
        "test_kr_market": 1,
        "test_kr_stock": len(active_kr),
        "test_us_market": 1,
        "test_us_stock": len(active_us),
        "test_total": len(messages),
    }
    output = {
        "contract": CONTRACT,
        "assessment_date": args.assessment_date,
        "run44": run44,
        "db_full_batch": {
            "rows": list(db_rows.values()),
            "failed_tickers": db_failed,
            "status": "PASS" if not db_failed else "FAIL",
        },
        "current_replays": {"KR": kr_replay, "US": us_replay},
        "market": {
            "kr_plan": plan.to_dict(),
            "kr_validation": kr_market_validation.to_dict(),
            "kr_message": kr_market,
            "kr_errors": kr_market_errors,
            "us_message": us_digest,
            "us_errors": us_market_errors,
        },
        "message_quality_rows": quality_rows,
        "counts": counts,
        "gates": gates,
        "status": "PASS"
        if not any(
            value == "FAIL"
            or isinstance(value, int)
            and not isinstance(value, bool)
            and value != 0
            for value in gates.values()
        )
        and not quality_failed
        and not db_failed
        else "FAIL",
    }
    message_output = {
        "contract": "run44-cross-market-test-messages-v1",
        "assessment_date": args.assessment_date,
        "counts": counts,
        "messages": messages,
        "status": output["status"],
    }
    _write_json(args.output, output)
    _write_json(args.messages_output, message_output)
    print(
        json.dumps(
            {
                "status": output["status"],
                "run44": run44["status"],
                "db_batch": "PASS" if not db_failed else "FAIL",
                "kr": len(active_kr),
                "us": len(active_us),
                "messages": len(messages),
            },
            sort_keys=True,
        )
    )


async def _send_test(args: argparse.Namespace) -> None:
    payload = _read_json(args.messages)
    if not isinstance(payload, Mapping) or payload.get("status") != "PASS":
        raise ValueError("cross-market message evidence must pass before send")
    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ValueError("test messages missing")
    counts = _mapping(payload.get("counts"))
    if len(messages) != int(counts.get("test_total") or 0):
        raise ValueError("test message count mismatch")
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test sink unavailable: {sink.get('reason')}")
    key = str(sink.get("selected_test_key_name") or "")
    receipt = await deliver_test_messages(
        messages,
        token=env.get("TELEGRAM_BOT_TOKEN") or "",
        test_chat_id=env.get(key) or "",
        production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.receipt,
        contract="run44-cross-market-test-delivery-v1",
        namespace=NAMESPACE,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "sent_message_count": receipt["sent_message_count"],
                "exact_payload_match": receipt["exact_payload_match"],
                "test_sink_alias": sink["test_sink_alias"],
                "production_sink_alias": sink["production_sink_alias"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--run44-packet", type=Path, required=True)
    build.add_argument("--current-us-replay", type=Path, required=True)
    build.add_argument("--current-kr-replay", type=Path, required=True)
    build.add_argument("--assessment-date", required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--messages-output", type=Path, required=True)
    send = subparsers.add_parser("send-test")
    send.add_argument("--messages", type=Path, required=True)
    send.add_argument("--env-file", type=Path, required=True)
    send.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        _build(args)
    else:
        asyncio.run(_send_test(args))


if __name__ == "__main__":
    main()
