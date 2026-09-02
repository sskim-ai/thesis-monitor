from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from app.config import get_settings
from app.services.accepted_decision_v2_runtime_service import (
    REASONING_EFFORT,
    REASONING_MODEL,
    AcceptedV2ProductionArtifact,
)
from app.services.us_market_message_quality_service import (
    validate_us_market_message_payload,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values
from scripts.v2_production_cutover_preflight import _production_payloads


CONTRACT = "run51-krx-night-test-delivery-v1"
NAMESPACE = "RUN51_KRX_NIGHT_LIVE_PATH_TEST_ONLY"
PACKET_ID = "2026-09-02-us-run-51-39a4d4eec53e"
EXPECTED_TICKERS = (
    "CORZ",
    "CPNG",
    "CRCL",
    "GOOGL",
    "HUT",
    "IBM",
    "MU",
    "RXRX",
    "SKHY",
    "SNDK",
    "TSLA",
    "TSM",
    "WRD",
    "WULF",
)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


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
    return hashlib.sha256(value.encode()).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_fingerprint(path: Path) -> dict[str, object]:
    rows = [
        {
            "path": str(item.relative_to(path)),
            "size": item.stat().st_size,
            "sha256": _sha256_file(item),
        }
        for item in sorted(path.rglob("*"))
        if item.is_file()
    ]
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return {
        "exists": path.exists(),
        "file_count": len(rows),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _file_fingerprint(path: Path) -> dict[str, object]:
    return {
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else None,
        "sha256": _sha256_file(path) if path.exists() else None,
    }


def _production_snapshot(production_root: Path, packet_dir: Path) -> dict[str, object]:
    return {
        "contract": "run51-production-mutation-snapshot-v1",
        "frozen_run51_archive": _tree_fingerprint(packet_dir),
        "accepted_decision_state": _file_fingerprint(
            production_root / "data/ai_review/decision_v2/state.json"
        ),
        "pilot_state_v3": _file_fingerprint(
            production_root / "data/ai_review/pilot/state-v3.json"
        ),
        "data_database": _file_fingerprint(
            production_root / "data/thesis_monitor.sqlite3"
        ),
        "root_database": _file_fingerprint(
            production_root / "thesis_monitor.sqlite3"
        ),
    }


def _received_quality(text: str) -> dict[str, object]:
    if text.startswith("🇺🇸 미국시장 마감"):
        return validate_us_market_message_payload(text).to_dict()
    return {
        "contract": "run51-stock-received-payload-integrity-v1",
        "status": "PASS" if text.strip() and len(text) <= 4096 else "FAIL",
        "nonempty": bool(text.strip()),
        "character_count": len(text),
    }


def _messages(
    artifact: AcceptedV2ProductionArtifact,
    *,
    deterministic_path: Path,
    enriched_market_path: Path,
) -> list[dict[str, object]]:
    enriched = _read_json(enriched_market_path)
    market_text = str(enriched.get("market_message") or "")
    market_quality = validate_us_market_message_payload(market_text)
    if market_quality.status != "PASS":
        raise ValueError("run51_enriched_market_quality_failed")
    stock_messages = _production_payloads((artifact,), (deterministic_path,))
    by_ticker = {str(row["ticker"]): row for row in stock_messages}
    if tuple(artifact.selected_subjects) != EXPECTED_TICKERS:
        raise ValueError("run51_v2_subject_order_or_scope_mismatch")
    if set(by_ticker) != set(EXPECTED_TICKERS):
        raise ValueError("run51_v2_payload_scope_mismatch")
    messages = [
        {
            "ticker": "MARKET",
            "route": "MARKET_ENRICHED",
            "text": market_text,
            "logical_identity": f"{NAMESPACE}:{PACKET_ID}:MARKET",
            "rendered_sha256": _sha256_text(market_text),
        }
    ]
    for ticker in EXPECTED_TICKERS:
        row = dict(by_ticker[ticker])
        row["logical_identity"] = f"{NAMESPACE}:{PACKET_ID}:{ticker}"
        messages.append(row)
    return messages


def _preflight(
    messages: Sequence[Mapping[str, object]],
    artifact: AcceptedV2ProductionArtifact,
    sink: Mapping[str, object],
) -> dict[str, object]:
    identities = [str(row.get("logical_identity") or "") for row in messages]
    tickers = [str(row.get("ticker") or "") for row in messages]
    hashes_valid = all(
        str(row.get("rendered_sha256") or "")
        == _sha256_text(str(row.get("text") or ""))
        for row in messages
    )
    max_chars = max(len(str(row.get("text") or "")) for row in messages)
    checks = {
        "artifact_status_pass": artifact.status == "PASS",
        "context_ready_count_14": len(artifact.selected_subjects) == 14,
        "accepted_ready_count_14": artifact.ready_count == 14,
        "not_ready_count_0": artifact.not_ready_count == 0,
        "reasoning_model_exact": artifact.reasoning_model == REASONING_MODEL,
        "reasoning_effort_xhigh": artifact.reasoning_effort == REASONING_EFFORT,
        "message_quality_pass": artifact.message_quality.get("status") == "PASS",
        "message_count_15": len(messages) == 15,
        "market_count_1": tickers.count("MARKET") == 1,
        "stock_count_14": len([ticker for ticker in tickers if ticker != "MARKET"])
        == 14,
        "ticker_scope_exact": tuple(tickers[1:]) == EXPECTED_TICKERS,
        "logical_identity_unique": len(identities) == len(set(identities)),
        "payload_hashes_valid": hashes_valid,
        "telegram_length_valid": max_chars
        <= get_settings().telegram_message_max_chars,
        "test_sink_available": sink.get("available") is True,
        "production_collision_0": sink.get("production_collision") == 0,
    }
    return {
        "contract": "run51-pre-send-atomic-readiness-v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "message_count": len(messages),
        "market_message_count": tickers.count("MARKET"),
        "stock_message_count": len([ticker for ticker in tickers if ticker != "MARKET"]),
        "max_character_count": max_chars,
        "test_sink_alias": sink.get("test_sink_alias"),
        "production_sink_alias": sink.get("production_sink_alias"),
        "production_recipient_resolution_disabled": True,
    }


def _prepare(args: argparse.Namespace) -> None:
    artifact = AcceptedV2ProductionArtifact.model_validate(_read_json(args.artifact))
    if artifact.packet_id != PACKET_ID:
        raise ValueError("run51_v2_artifact_packet_mismatch")
    values = load_env_values(args.env_file)
    sink = audit_test_sink(values)
    messages = _messages(
        artifact,
        deterministic_path=args.deterministic,
        enriched_market_path=args.enriched_market,
    )
    preflight = _preflight(messages, artifact, sink)
    if preflight["status"] != "PASS":
        raise ValueError("run51_pre_send_atomic_readiness_failed")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if (args.output_dir / "test-sink-receipt.json").exists():
        raise FileExistsError("run51_test_receipt_already_exists")
    _write_json(
        args.output_dir / "production-payloads.json",
        {
            "contract": CONTRACT,
            "namespace": NAMESPACE,
            "packet_id": PACKET_ID,
            "messages": messages,
        },
    )
    _write_json(args.output_dir / "pre-send-readiness.json", preflight)
    _write_json(
        args.output_dir / "production-before.json",
        _production_snapshot(args.production_root, args.packet_dir),
    )
    print(json.dumps(preflight, ensure_ascii=False, sort_keys=True))


async def _send(args: argparse.Namespace) -> None:
    payload = _read_json(args.output_dir / "production-payloads.json")
    messages = [
        row for row in payload.get("messages") or () if isinstance(row, Mapping)
    ]
    preflight = _read_json(args.output_dir / "pre-send-readiness.json")
    if preflight.get("status") != "PASS" or len(messages) != 15:
        raise ValueError("run51_send_without_atomic_readiness")
    values = load_env_values(args.env_file)
    sink = audit_test_sink(values)
    if sink.get("available") is not True or sink.get("production_collision") != 0:
        raise ValueError("run51_test_sink_unavailable_or_colliding")
    selected_key = str(sink.get("selected_test_key_name") or "")
    receipt = await deliver_test_messages(
        messages,
        token=values.get("TELEGRAM_BOT_TOKEN", ""),
        test_chat_id=values.get(selected_key, ""),
        production_chat_id=values.get("TELEGRAM_CHAT_ID", ""),
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.output_dir / "test-sink-receipt.json",
        contract=CONTRACT,
        namespace=NAMESPACE,
        received_payload_validator=_received_quality,
    )
    before = _read_json(args.output_dir / "production-before.json")
    after = _production_snapshot(args.production_root, args.packet_dir)
    _write_json(args.output_dir / "production-after.json", after)
    mutation_diff = {
        key: before.get(key) != after.get(key)
        for key in (
            "frozen_run51_archive",
            "accepted_decision_state",
            "pilot_state_v3",
            "data_database",
            "root_database",
        )
    }
    production_mutations = sum(mutation_diff.values())
    delivery = {
        "contract": CONTRACT,
        "namespace": NAMESPACE,
        "status": (
            "PASS"
            if receipt.get("status") == "sent"
            and receipt.get("sent_message_count") == 15
            and receipt.get("exact_payload_match") is True
            and production_mutations == 0
            else "FAIL"
        ),
        "planned_message_count": 15,
        "sent_message_count": receipt.get("sent_message_count"),
        "acknowledged_message_count": len(receipt.get("rows") or ()),
        "duplicate_count": receipt.get("duplicate_count"),
        "orphan_count": receipt.get("orphan_count"),
        "unowned_retry_count": receipt.get("unowned_retry_count"),
        "acknowledged_message_resend": 0,
        "exact_payload_match": receipt.get("exact_payload_match"),
        "real_telegram_transport": receipt.get("status") == "sent",
        "test_sink_alias": sink.get("test_sink_alias"),
        "production_sink_alias": sink.get("production_sink_alias"),
        "production_recipient_send": receipt.get(
            "production_recipient_send_count", 0
        ),
        "production_recipient_resolution_disabled": True,
        "production_mutation_diff": mutation_diff,
        "production_state_mutations": production_mutations,
        "receipt": receipt,
    }
    _write_json(args.output_dir / "delivery.json", delivery)
    print(json.dumps(delivery, ensure_ascii=False, sort_keys=True))


async def _run(args: argparse.Namespace) -> None:
    if args.command == "prepare":
        _prepare(args)
    else:
        await _send(args)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "send"))
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--deterministic", type=Path, required=True)
    parser.add_argument("--enriched-market", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--production-root", type=Path, required=True)
    parser.add_argument("--packet-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
