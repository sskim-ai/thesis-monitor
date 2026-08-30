from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from app.services.cross_market_decision_engine_service import (
    DecisionCandidate,
    DecisionEvidencePacket,
)
from app.services.decision_canary_service import (
    decision_korean_localization_errors,
    decision_polarity_errors,
    insert_decision_canary_block,
    render_decision_canary_block,
)
from app.services.us_full_message_service import render_us_full_market_message
from app.services.us_market_digest_plan_service import build_us_market_digest_plan
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "us-market-decision-localization-cleanup-v1"
NAMESPACE = "US_MARKET_DECISION_LOCALIZATION_CLEANUP_TEST_ONLY"
MESSAGE_KEYS = ("US_MARKET", "003690", "000660", "GOOGL", "RXRX")
EXPECTED_DECISIONS = {
    "003690": "HOLD",
    "000660": "HOLD",
    "GOOGL": "HOLD",
    "RXRX": "SELL",
}
INDEX_TYPES = {
    "SPY": ("market_index", "S&P500"),
    "QQQ": ("market_index", "Nasdaq"),
    "IWM": ("market_index", "Russell 2000"),
    "SOXX": ("market_sector", "반도체"),
    "RSP": ("market_style", "S&P500 동일가중"),
}
SECTOR_LABELS = {
    "XLB": "소재",
    "XLC": "커뮤니케이션 서비스",
    "XLE": "에너지",
    "XLF": "금융",
    "XLI": "산업재",
    "XLK": "정보기술",
    "XLP": "필수소비재",
    "XLRE": "부동산",
    "XLU": "유틸리티",
    "XLV": "헬스케어",
    "XLY": "경기소비재",
}


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _market_context(collection: Mapping[str, object]) -> dict[str, object]:
    market = collection.get("us_market")
    if not isinstance(market, Mapping):
        raise ValueError("us_market_evidence_missing")
    rows = [row for row in market.get("rows") or () if isinstance(row, Mapping)]
    facts: list[dict[str, object]] = []
    session_dates: set[str] = set()
    for row in rows:
        symbol = str(row.get("symbol") or "")
        metadata = INDEX_TYPES.get(symbol)
        if metadata is None and symbol in SECTOR_LABELS:
            metadata = ("market_sector", SECTOR_LABELS[symbol])
        if metadata is None:
            continue
        fact_type, label = metadata
        session_date = str(row.get("session_date") or "")
        session_dates.add(session_date)
        facts.append(
            {
                "fact_id": f"market:{fact_type.removeprefix('market_')}:{symbol}",
                "fact_type": fact_type,
                "as_of_date": session_date,
                "fields": {
                    "series_code": symbol,
                    "label": label,
                    "return_pct": float(row["return_pct"]),
                    "temporal_role": "CURRENT_OBSERVATION",
                    "today_signal_eligible": True,
                    "structured_state": "CURRENT_DIRECTIONAL",
                },
            }
        )
    if len(session_dates) != 1:
        raise ValueError("us_market_session_identity_invalid")
    context: dict[str, object] = {
        "fact_catalog": facts,
        "key_change_fact_ids": [],
        "coverage": {
            "breadth": {
                "status": "unavailable",
                "reason": "exact_session_not_published",
            }
        },
    }
    context["us_market_digest_plan"] = build_us_market_digest_plan(context).to_dict()
    return context


def _message_quality(key: str, text: str) -> list[str]:
    if key == "US_MARKET":
        required = (
            "🇺🇸 미국시장 마감",
            "• SPY -0.23%",
            "• QQQ -0.65%",
            "• IWM -1.35%",
            "• SOXX -3.20%",
            "• RSP -0.34%",
            "동일가중 S&P500",
            "소형주 IWM도 SPY보다 약해",
            "반도체 SOXX가 SPY를 크게 밑돌아",
            "• 업종 강세:",
            "• 업종 약세:",
        )
    else:
        required = (
            f"AI 종합 판단: {EXPECTED_DECISIONS[key]}",
            "추론등급: 매우 높음",
            "✅ BUY 쪽 근거:",
            "⚠️ SELL 쪽 근거:",
            "🔼 상향 조건:",
            "🔽 하향 조건:",
        )
    errors = [f"missing:{token}" for token in required if token not in text]
    forbidden = (
        "DB손해보험",
        "DB Insurance",
        "시장가 매수",
        "시장가 매도",
        "전량 매도",
        "지금 사세요",
        "지금 파세요",
    )
    errors.extend(f"forbidden:{token}" for token in forbidden if token in text)
    return errors


def _build(args: argparse.Namespace) -> None:
    collection = _read_json(args.collection)
    decisions = _read_json(args.decisions)
    if not isinstance(collection, Mapping) or not isinstance(decisions, Mapping):
        raise ValueError("cleanup_inputs_invalid")
    base_messages = collection.get("base_messages")
    if not isinstance(base_messages, Mapping):
        raise ValueError("base_messages_missing")
    decision_rows = {
        str(row.get("ticker") or ""): row
        for row in decisions.get("rows") or ()
        if isinstance(row, Mapping)
    }
    if set(decision_rows) != set(EXPECTED_DECISIONS):
        raise ValueError("decision_subjects_mismatch")

    market_context = _market_context(collection)
    rendered_market = render_us_full_market_message(market_context)
    if rendered_market.status != "PASS":
        raise ValueError("us_market_render_failed:" + ",".join(rendered_market.validation_errors))
    messages: list[dict[str, object]] = []
    quality: list[dict[str, object]] = []
    market_errors = _message_quality("US_MARKET", rendered_market.text)
    if market_errors:
        raise ValueError("us_market_message_quality:" + ",".join(market_errors))
    messages.append(
        {
            "ticker": "US_MARKET",
            "route": "DEDICATED_NON_PRODUCTION_TEST_SINK_ONLY",
            "logical_identity": f"{NAMESPACE}:US_MARKET",
            "text": rendered_market.text,
        }
    )
    quality.append(
        {
            "ticker": "US_MARKET",
            "status": "PASS",
            "payload_sha256": _sha256_text(rendered_market.text),
            "character_count": len(rendered_market.text),
            "market_internal_line_count": rendered_market.text.count("\n• ") - 7,
        }
    )

    decision_semantics: list[dict[str, object]] = []
    for ticker in MESSAGE_KEYS[1:]:
        row = decision_rows[ticker]
        packet = DecisionEvidencePacket.model_validate(row["evidence_packet"])
        candidate = DecisionCandidate.model_validate(row["candidate"])
        if candidate.decision != EXPECTED_DECISIONS[ticker]:
            raise ValueError(f"same_evidence_decision_changed:{ticker}")
        polarity_errors = decision_polarity_errors(packet, candidate)
        if polarity_errors:
            raise ValueError(f"decision_polarity_invalid:{ticker}")
        localization_errors = decision_korean_localization_errors(packet, candidate)
        if localization_errors:
            raise ValueError(
                f"decision_localization_invalid:{ticker}:" + ",".join(localization_errors)
            )
        block = render_decision_canary_block(packet, candidate)
        base = base_messages.get(ticker)
        if not isinstance(base, Mapping):
            raise ValueError(f"base_message_missing:{ticker}")
        base_text = str(base.get("text") or "")
        message = insert_decision_canary_block(base_text, block.text)
        errors = _message_quality(ticker, message)
        if ticker == "003690" and "🏢 코리안리(003690)" not in message:
            errors.append("canonical_identity_missing")
        if errors:
            raise ValueError(f"stock_message_quality:{ticker}:" + ",".join(errors))
        messages.append(
            {
                "ticker": ticker,
                "route": "DEDICATED_NON_PRODUCTION_TEST_SINK_ONLY",
                "logical_identity": f"{NAMESPACE}:{ticker}",
                "text": message,
            }
        )
        quality.append(
            {
                "ticker": ticker,
                "decision": candidate.decision,
                "status": "PASS",
                "payload_sha256": _sha256_text(message),
                "base_payload_sha256": _sha256_text(base_text),
                "character_count": len(message),
                "korean_localization_error_count": len(localization_errors),
                "polarity_error_count": len(polarity_errors),
            }
        )
        decision_semantics.append(
            {
                "ticker": ticker,
                "decision": candidate.decision,
                "confidence": candidate.confidence,
                "horizon": candidate.horizon,
                "timing": candidate.timing,
                "buy_refs": sorted(
                    ref for claim in candidate.buy_case_evidence for ref in claim.evidence_refs
                ),
                "sell_refs": sorted(
                    ref for claim in candidate.sell_case_evidence for ref in claim.evidence_refs
                ),
            }
        )

    if tuple(str(row["ticker"]) for row in messages) != MESSAGE_KEYS:
        raise ValueError("test_message_order_invalid")
    identities = [str(row["logical_identity"]) for row in messages]
    if len(identities) != len(set(identities)):
        raise ValueError("test_message_identity_duplicate")
    plan = market_context["us_market_digest_plan"]
    _write_json(
        args.output,
        {
            "contract": CONTRACT,
            "status": "PASS",
            "namespace": NAMESPACE,
            "message_count": 5,
            "production_recipient_send_count": 0,
            "production_delivery_intent_count": 0,
            "natural_canary_counter_mutation_count": 0,
            "messages": messages,
            "quality": quality,
            "decision_semantics": decision_semantics,
            "us_market_digest_plan": plan,
            "safety": {
                "ai_calculated_relative_spread": 0,
                "rsp_as_exchange_breadth": 0,
                "posthoc_freeform_translation_as_source_of_truth": 0,
                "renderer_only_003690_name_patch": 0,
            },
        },
    )
    print(json.dumps({"status": "PASS", "messages": 5}, sort_keys=True))


def _received_quality(message: str) -> Mapping[str, object]:
    if message.startswith("🇺🇸"):
        errors = _message_quality("US_MARKET", message)
    else:
        ticker = next((item for item in EXPECTED_DECISIONS if f"({item})" in message), "")
        errors = _message_quality(ticker, message) if ticker else ["ticker_unresolved"]
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


async def _send(args: argparse.Namespace) -> None:
    payload = _read_json(args.messages)
    if not isinstance(payload, Mapping) or payload.get("status") != "PASS":
        raise ValueError("test_messages_not_ready")
    messages = [row for row in payload.get("messages") or () if isinstance(row, Mapping)]
    if len(messages) != 5:
        raise ValueError("test_message_count_not_five")
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test_sink_unavailable:{sink.get('reason')}")
    selected_key = str(sink.get("selected_test_key_name") or "")
    receipt = await deliver_test_messages(
        messages,
        token=env.get("TELEGRAM_BOT_TOKEN") or "",
        test_chat_id=env.get(selected_key) or "",
        production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.receipt,
        contract="us-market-decision-localization-cleanup-test-sink-v1",
        namespace=NAMESPACE,
        received_payload_validator=_received_quality,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "sent": receipt["sent_message_count"],
                "exact": receipt["exact_payload_match"],
                "production_recipient_send": receipt["production_recipient_send_count"],
            },
            sort_keys=True,
        )
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--collection", type=Path, required=True)
    build.add_argument("--decisions", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    send = subparsers.add_parser("send-test")
    send.add_argument("--env-file", type=Path, required=True)
    send.add_argument("--messages", type=Path, required=True)
    send.add_argument("--receipt", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "build":
        _build(args)
    else:
        asyncio.run(_send(args))


if __name__ == "__main__":
    main()
