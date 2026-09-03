from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2ProductionArtifact,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values
from scripts.v2_production_cutover_preflight import _production_payloads


CONTRACT = "packet-ai-consumability-test-sink-v1"
NAMESPACE = "PACKET_AI_CONSUMABILITY_20260903_TEST_ONLY"


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _messages(args: argparse.Namespace) -> list[dict[str, object]]:
    artifact_value = _read_json(args.us_artifact)
    if not isinstance(artifact_value, Mapping):
        raise ValueError("us_artifact_invalid")
    artifact = AcceptedV2ProductionArtifact.model_validate(artifact_value)
    if artifact.market != "us" or len(artifact.selected_subjects) != 14:
        raise ValueError("us_14_subject_artifact_required")
    us_messages = [
        row
        for row in _production_payloads((artifact,), (args.us_deterministic,))
        if row.get("route") == "V2_ACCEPTED"
    ]
    kr_value = _read_json(args.kr_sanitized_messages)
    if not isinstance(kr_value, Mapping):
        raise ValueError("kr_sanitized_messages_invalid")
    kr_messages = [
        {
            "ticker": str(row.get("ticker") or ""),
            "route": str(row.get("route") or ""),
            "text": str(row.get("text") or ""),
        }
        for row in kr_value.get("messages") or ()
        if isinstance(row, Mapping)
        and row.get("market") == "kr"
        and row.get("route") == "V2_ACCEPTED"
    ]
    if len(kr_messages) != 8 or len(us_messages) != 14:
        raise ValueError("test_sink_requires_kr8_us14")
    messages = [
        {
            **row,
            "logical_identity": (
                f"{NAMESPACE}:{market}:{str(row.get('ticker') or '')}"
            ),
            "rendered_sha256": _sha256_text(str(row.get("text") or "")),
        }
        for market, rows in (("kr", kr_messages), ("us", us_messages))
        for row in rows
    ]
    identities = [str(row["logical_identity"]) for row in messages]
    if len(messages) != 22 or len(identities) != len(set(identities)):
        raise ValueError("test_sink_message_identity_invalid")
    return messages


async def _run(args: argparse.Namespace) -> None:
    messages = _messages(args)
    values = load_env_values(args.env_file)
    sink = audit_test_sink(values)
    if sink.get("available") is not True or sink.get("production_collision") != 0:
        raise ValueError("dedicated_test_sink_unavailable_or_not_isolated")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.output_dir / "messages.json", {"messages": messages})
    safe_sink = {
        key: value
        for key, value in sink.items()
        if key not in {"test_sink_alias", "production_sink_alias"}
    }
    summary = {
        "contract": CONTRACT,
        "namespace": NAMESPACE,
        "planned_message_count": 22,
        "kr_message_count": 8,
        "us_message_count": 14,
        "test_sink": safe_sink,
        "production_recipient_send": 0,
        "production_delivery_intent_created": 0,
        "status": "READY_TO_SEND",
    }
    if args.send:
        receipt = await deliver_test_messages(
            messages,
            token=values.get("TELEGRAM_BOT_TOKEN", ""),
            test_chat_id=values.get(str(sink["selected_test_key_name"]), ""),
            production_chat_id=values.get("TELEGRAM_CHAT_ID", ""),
            test_sink_alias=str(sink["test_sink_alias"]),
            production_sink_alias=str(sink["production_sink_alias"]),
            receipt_path=args.output_dir / "receipt.json",
            contract=CONTRACT,
            namespace=NAMESPACE,
            inter_message_delay_seconds=3.1,
        )
        summary.update(
            {
                "status": "PASS" if receipt.get("status") == "sent" else "FAIL",
                "sent_message_count": receipt.get("sent_message_count"),
                "exact_payload_match": receipt.get("exact_payload_match"),
                "duplicate_count": receipt.get("duplicate_count"),
                "orphan_count": receipt.get("orphan_count"),
                "production_recipient_send": receipt.get(
                    "production_recipient_send_count"
                ),
                "production_delivery_intent_created": receipt.get(
                    "production_intent_created"
                ),
            }
        )
    _write_json(args.summary, summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--us-artifact", type=Path, required=True)
    parser.add_argument("--us-deterministic", type=Path, required=True)
    parser.add_argument("--kr-sanitized-messages", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--send", action="store_true")
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
