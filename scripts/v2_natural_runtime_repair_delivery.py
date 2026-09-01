from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Mapping
from pathlib import Path

from app.services.accepted_decision_v2_runtime_service import (
    REASONING_EFFORT,
    REASONING_MODEL,
    AcceptedV2ProductionArtifact,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values
from scripts.v2_production_cutover_preflight import _production_payloads


CONTRACT = "v2-natural-runtime-repair-test-sink-v1"
NAMESPACE = "V2_NATURAL_RUNTIME_REPAIR_20260901_TEST_ONLY"


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sink(args: argparse.Namespace) -> tuple[dict[str, object], dict[str, str]]:
    values = load_env_values(args.env_file)
    sink = audit_test_sink(values)
    if sink.get("available") is not True or sink.get("production_collision") != 0:
        raise ValueError("dedicated_test_sink_unavailable_or_not_isolated")
    return sink, values


def _summary(
    artifacts: tuple[AcceptedV2ProductionArtifact, ...],
    *,
    sink: Mapping[str, object],
    receipt: Mapping[str, object] | None = None,
) -> dict[str, object]:
    sent = int((receipt or {}).get("sent_message_count") or 0)
    exact = bool((receipt or {}).get("exact_payload_match"))
    return {
        "contract": CONTRACT,
        "namespace": NAMESPACE,
        "status": "PASS" if sent == 22 and exact else "READY_TO_SEND",
        "markets": {
            artifact.market: {
                "packet_id": artifact.packet_id,
                "subject_count": len(artifact.selected_subjects),
                "ready_count": artifact.ready_count,
                "not_ready_count": artifact.not_ready_count,
                "message_quality": artifact.message_quality,
            }
            for artifact in artifacts
        },
        "subject_count": sum(len(artifact.selected_subjects) for artifact in artifacts),
        "test_sink": dict(sink),
        "sent_message_count": sent,
        "test_sink_exact_payload": exact,
        "production_recipient_send": 0,
        "production_delivery_intent_created": 0,
        "reasoning_model": REASONING_MODEL,
        "reasoning_effort": REASONING_EFFORT,
    }


def _load_artifacts(args: argparse.Namespace) -> tuple[AcceptedV2ProductionArtifact, ...]:
    artifacts = tuple(
        AcceptedV2ProductionArtifact.model_validate(_read_json(path))
        for path in (args.kr_artifact, args.us_artifact)
    )
    if [artifact.market for artifact in artifacts] != ["kr", "us"]:
        raise ValueError("repair_test_sink_market_order_invalid")
    if [len(artifact.selected_subjects) for artifact in artifacts] != [8, 14]:
        raise ValueError("repair_test_sink_subject_scope_invalid")
    if any(artifact.ready_count != len(artifact.selected_subjects) for artifact in artifacts):
        raise ValueError("repair_test_sink_artifact_not_ready")
    return artifacts


def _build(args: argparse.Namespace) -> None:
    artifacts = _load_artifacts(args)
    messages = _production_payloads(
        artifacts,
        (args.kr_deterministic, args.us_deterministic),
    )
    for row in messages:
        row["logical_identity"] = f"{NAMESPACE}:{row['ticker']}"
    if len(messages) != 22 or len({str(row["logical_identity"]) for row in messages}) != 22:
        raise ValueError("repair_test_sink_exact_scope_invalid")
    sink, _ = _sink(args)
    _write_json(args.output_dir / "production-payloads.json", {"messages": messages})
    summary = _summary(artifacts, sink=sink)
    _write_json(args.output_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


async def _send(args: argparse.Namespace) -> None:
    artifacts = _load_artifacts(args)
    messages = [
        row
        for row in _read_json(args.output_dir / "production-payloads.json").get(
            "messages", []
        )
        if isinstance(row, Mapping)
    ]
    if len(messages) != 22:
        raise ValueError("repair_test_sink_payload_count_invalid")
    sink, values = _sink(args)
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
    )
    summary = _summary(artifacts, sink=sink, receipt=receipt)
    _write_json(args.output_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


async def _resume(args: argparse.Namespace) -> None:
    artifacts = _load_artifacts(args)
    messages = [
        row
        for row in _read_json(args.output_dir / "production-payloads.json").get(
            "messages", []
        )
        if isinstance(row, Mapping)
    ]
    receipt_paths = [
        args.output_dir / "test-sink-receipt.json",
        *sorted(args.output_dir.glob("test-sink-continuation-receipt*.json")),
    ]
    receipts = [_read_json(path) for path in receipt_paths]
    if any(
        receipt.get("status") != "failed"
        or receipt.get("safe_error") != "http_status_429"
        for receipt in receipts
    ):
        raise ValueError("repair_test_sink_resume_requires_429")
    prior_rows = [
        dict(row)
        for receipt in receipts
        for row in receipt.get("rows") or ()
        if isinstance(row, Mapping)
    ]
    expected = {str(row.get("logical_identity") or ""): row for row in messages}
    sent = {str(row.get("logical_identity") or "") for row in prior_rows}
    if (
        len(expected) != 22
        or len(sent) != len(prior_rows)
        or any(
            row.get("exact_payload_match") is not True
            or row.get("rendered_sha256")
            != expected[str(row.get("logical_identity") or "")].get("rendered_sha256")
            for row in prior_rows
        )
    ):
        raise ValueError("repair_test_sink_initial_receipt_invalid")
    remaining = [
        row for row in messages if str(row.get("logical_identity") or "") not in sent
    ]
    if not remaining or len(prior_rows) + len(remaining) != 22:
        raise ValueError("repair_test_sink_remaining_subset_invalid")
    sink, values = _sink(args)
    selected_key = str(sink.get("selected_test_key_name") or "")
    continuation_number = len(receipt_paths)
    continuation_path = args.output_dir / (
        "test-sink-continuation-receipt.json"
        if continuation_number == 1
        else f"test-sink-continuation-receipt-{continuation_number:02d}.json"
    )
    continuation = await deliver_test_messages(
        remaining,
        token=values.get("TELEGRAM_BOT_TOKEN", ""),
        test_chat_id=values.get(selected_key, ""),
        production_chat_id=values.get("TELEGRAM_CHAT_ID", ""),
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=continuation_path,
        contract=f"{CONTRACT}-continuation",
        namespace=NAMESPACE,
    )
    continuation_rows = [
        dict(row)
        for row in continuation.get("rows") or ()
        if isinstance(row, Mapping)
    ]
    for index, row in enumerate(continuation_rows, start=len(prior_rows) + 1):
        row["sequence"] = index
    rows = [*prior_rows, *continuation_rows]
    identities = [str(row.get("logical_identity") or "") for row in rows]
    exact = (
        len(rows) == 22
        and len(identities) == len(set(identities))
        and set(identities) == set(expected)
        and all(row.get("exact_payload_match") is True for row in rows)
    )
    final = {
        "contract": f"{CONTRACT}-reconciliation",
        "namespace": NAMESPACE,
        "status": "sent" if exact else "failed",
        "test_sink_alias": sink["test_sink_alias"],
        "production_sink_alias": sink["production_sink_alias"],
        "planned_message_count": 22,
        "sent_message_count": len(rows),
        "initial_sent_count": len(
            [
                row
                for row in receipts[0].get("rows") or ()
                if isinstance(row, Mapping)
            ]
        ),
        "continuation_sent_count": len(rows)
        - len(
            [
                row
                for row in receipts[0].get("rows") or ()
                if isinstance(row, Mapping)
            ]
        ),
        "continuation_attempt_count": len(receipts),
        "rate_limit_recovery": True,
        "exact_payload_match": exact,
        "duplicate_count": len(identities) - len(set(identities)),
        "orphan_count": len(set(identities) - set(expected)),
        "production_collision": 0,
        "production_intent_created": 0,
        "production_recipient_send_count": 0,
        "rows": rows,
    }
    _write_json(args.output_dir / "test-sink-final-receipt.json", final)
    summary = _summary(artifacts, sink=sink, receipt=final)
    _write_json(args.output_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kr-artifact", type=Path, required=True)
    parser.add_argument("--us-artifact", type=Path, required=True)
    parser.add_argument("--kr-deterministic", type=Path, required=True)
    parser.add_argument("--us-deterministic", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if sum((args.build, args.send, args.resume)) != 1:
        raise ValueError("choose_exactly_one_operation")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.build:
        _build(args)
    elif args.send:
        asyncio.run(_send(args))
    else:
        asyncio.run(_resume(args))


if __name__ == "__main__":
    main()
