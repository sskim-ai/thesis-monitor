from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

import httpx

from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "kr-final-preenable-test-delivery-v1"
MARKET_KEY = "__DAILY_DIGEST_KR__"
NAMESPACE = "TEST_ONLY_NON_PRODUCTION"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _message_text(row: Mapping[str, object]) -> str:
    value = row.get("text")
    if isinstance(value, str):
        return value
    payload = row.get("payload")
    if isinstance(payload, Mapping) and isinstance(payload.get("text"), str):
        return str(payload["text"])
    raise ValueError("message text missing")


def build_delivery_messages(
    *,
    packet_path: Path,
    ai_messages_path: Path,
    price_audit_path: Path,
    market_preview_path: Path,
) -> tuple[str, list[dict[str, object]]]:
    packet = _read_json(packet_path)
    ai_payload = _read_json(ai_messages_path)
    price_audit = _read_json(price_audit_path)
    if not isinstance(packet, Mapping) or not isinstance(ai_payload, Mapping):
        raise ValueError("packet or AI payload is invalid")
    if not isinstance(price_audit, Mapping):
        raise ValueError("price audit is invalid")

    packet_id = str(packet.get("packet_id") or "")
    stocks = packet.get("stocks")
    ai_rows = ai_payload.get("messages")
    price_rows = price_audit.get("rows")
    if not packet_id or not isinstance(stocks, list):
        raise ValueError("packet identity or stocks missing")
    if not isinstance(ai_rows, list) or not isinstance(price_rows, list):
        raise ValueError("AI messages or price rows missing")

    tickers = [
        str(row.get("ticker"))
        for row in stocks
        if isinstance(row, Mapping) and str(row.get("ticker") or "").isdigit()
    ]
    ai_by_ticker = {
        str(row.get("ticker")): row
        for row in ai_rows
        if isinstance(row, Mapping) and row.get("ticker")
    }
    price_by_ticker = {
        str(row.get("ticker")): row
        for row in price_rows
        if isinstance(row, Mapping) and row.get("ticker")
    }
    if set(tickers) != set(price_by_ticker) or MARKET_KEY not in ai_by_ticker:
        raise ValueError("current monitored KR message set is incomplete")

    market_preview = market_preview_path.read_text(encoding="utf-8")
    match = re.search(
        r"## Production-equivalent candidate\n\n```text\n(.*?)\n```",
        market_preview,
        re.DOTALL,
    )
    if match is None:
        raise ValueError("production-equivalent market candidate missing")

    market_ai = ai_by_ticker[MARKET_KEY]
    market_core = market_ai.get("common_ai_core")
    market_mode = (
        str(market_core.get("final_delivery_mode") or "AI")
        if isinstance(market_core, Mapping)
        else "AI"
    )
    messages: list[dict[str, object]] = [
        {
            "ticker": MARKET_KEY,
            "route": market_mode,
            "text": match.group(1),
            "logical_identity": f"{NAMESPACE}:{packet_id}:market",
        }
    ]
    for ticker in tickers:
        ai_row = ai_by_ticker.get(ticker)
        price_row = price_by_ticker[ticker]
        if not isinstance(ai_row, Mapping):
            raise ValueError(f"AI message missing for {ticker}")
        preview = price_row.get("ai_preview")
        if not isinstance(preview, str) or not preview:
            raise ValueError(f"price-structure preview missing for {ticker}")
        core = ai_row.get("common_ai_core")
        route = (
            str(core.get("final_delivery_mode") or "current_ai_existing")
            if isinstance(core, Mapping)
            else "current_ai_existing"
        )
        messages.append(
            {
                "ticker": ticker,
                "route": route,
                "text": preview,
                "logical_identity": f"{NAMESPACE}:{packet_id}:stock:{ticker}",
            }
        )

    identities = [str(row["logical_identity"]) for row in messages]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate test delivery identity")
    if any(len(str(row["text"])) > 3500 for row in messages):
        raise ValueError("test payload exceeds production message limit")
    return packet_id, messages


async def deliver_test_messages(
    messages: Sequence[Mapping[str, object]],
    *,
    token: str,
    test_chat_id: str,
    production_chat_id: str,
    test_sink_alias: str,
    production_sink_alias: str,
    receipt_path: Path,
    transport: httpx.AsyncBaseTransport | None = None,
    contract: str = CONTRACT,
    namespace: str = NAMESPACE,
) -> dict[str, object]:
    if not token or not test_chat_id or not production_chat_id:
        raise ValueError("Telegram credentials or recipient missing")
    if test_chat_id == production_chat_id:
        raise ValueError("test sink matches production recipient")
    if receipt_path.exists():
        raise FileExistsError("test receipt already exists; refusing duplicate send")

    receipt: dict[str, object] = {
        "contract": contract,
        "namespace": namespace,
        "status": "in_progress",
        "test_sink_alias": test_sink_alias,
        "production_sink_alias": production_sink_alias,
        "production_collision": 0,
        "production_intent_created": 0,
        "request_retry_count": 0,
        "planned_message_count": len(messages),
        "sent_message_count": 0,
        "rows": [],
    }
    _write_json(receipt_path, receipt)
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=30.0, transport=transport) as client:
        for index, message in enumerate(messages, start=1):
            text = str(message.get("text") or "")
            ticker = str(message.get("ticker") or "")
            rendered_sha = _sha256_text(text)
            try:
                response = await client.post(
                    endpoint,
                    json={
                        "chat_id": test_chat_id,
                        "text": text,
                        "disable_web_page_preview": True,
                    },
                )
            except httpx.HTTPError as exc:
                receipt["status"] = "failed"
                receipt["safe_error"] = type(exc).__name__
                _write_json(receipt_path, receipt)
                raise RuntimeError("Telegram test delivery network failure") from None
            if response.status_code != 200:
                receipt["status"] = "failed"
                receipt["safe_error"] = f"http_status_{response.status_code}"
                _write_json(receipt_path, receipt)
                raise RuntimeError("Telegram test delivery rejected")
            payload = response.json()
            result = payload.get("result") if isinstance(payload, Mapping) else None
            received_text = result.get("text") if isinstance(result, Mapping) else None
            message_id = result.get("message_id") if isinstance(result, Mapping) else None
            if payload.get("ok") is not True or not isinstance(received_text, str):
                receipt["status"] = "failed"
                receipt["safe_error"] = "invalid_telegram_response"
                _write_json(receipt_path, receipt)
                raise RuntimeError("Telegram test delivery response invalid")
            received_sha = _sha256_text(received_text)
            row = {
                "sequence": index,
                "ticker": ticker,
                "route": str(message.get("route") or ""),
                "logical_identity": str(message.get("logical_identity") or ""),
                "character_count": len(text),
                "rendered_sha256": rendered_sha,
                "outbound_sha256": rendered_sha,
                "received_sha256": received_sha,
                "exact_payload_match": received_sha == rendered_sha,
                "remote_message_alias": _sha256_text(
                    f"{test_chat_id}:{message_id}"
                )[:12],
                "send_attempts": 1,
            }
            rows = receipt["rows"]
            assert isinstance(rows, list)
            rows.append(row)
            receipt["sent_message_count"] = len(rows)
            _write_json(receipt_path, receipt)

    rows = receipt["rows"]
    assert isinstance(rows, list)
    exact = all(bool(row.get("exact_payload_match")) for row in rows)
    receipt["status"] = "sent" if exact and len(rows) == len(messages) else "failed"
    receipt["exact_payload_match"] = exact
    receipt["duplicate_count"] = 0
    receipt["orphan_count"] = 0
    receipt["unowned_retry_count"] = 0
    receipt["production_recipient_send_count"] = 0
    _write_json(receipt_path, receipt)
    return receipt


async def _run(args: argparse.Namespace) -> None:
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test sink unavailable: {sink.get('reason')}")
    selected_key = str(sink.get("selected_test_key_name") or "")
    packet_id, messages = build_delivery_messages(
        packet_path=args.packet,
        ai_messages_path=args.ai_messages,
        price_audit_path=args.price_audit,
        market_preview_path=args.market_preview,
    )
    summary = {
        "contract": CONTRACT,
        "namespace": NAMESPACE,
        "packet_id": packet_id,
        "test_sink_alias": sink["test_sink_alias"],
        "production_sink_alias": sink["production_sink_alias"],
        "production_collision": sink["production_collision"],
        "message_count": len(messages),
        "market_message_count": sum(row["ticker"] == MARKET_KEY for row in messages),
        "stock_message_count": sum(row["ticker"] != MARKET_KEY for row in messages),
        "max_character_count": max(len(str(row["text"])) for row in messages),
    }
    if not args.send:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return
    receipt = await deliver_test_messages(
        messages,
        token=env.get("TELEGRAM_BOT_TOKEN") or "",
        test_chat_id=env.get(selected_key) or "",
        production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.receipt_output,
    )
    print(
        json.dumps(
            {
                **summary,
                "status": receipt["status"],
                "sent_message_count": receipt["sent_message_count"],
                "exact_payload_match": receipt["exact_payload_match"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--ai-messages", type=Path, required=True)
    parser.add_argument("--price-audit", type=Path, required=True)
    parser.add_argument("--market-preview", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--send", action="store_true")
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
