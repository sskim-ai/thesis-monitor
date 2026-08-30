from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path

import httpx

from app.config import get_settings
from app.jobs.accepted_decision_v2_runtime import _fetch_ohlcv
from app.services.accepted_decision_v2_runtime_service import (
    REASONING_EFFORT,
    REASONING_MODEL,
    AcceptedV2ProductionBatchOutput,
    AcceptedV2ProductionContext,
    accepted_v2_production_prompt,
    build_accepted_v2_production_context,
    validate_accepted_v2_production_output,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    build_decision_evidence_packet,
)
from app.services.decision_canary_service import (
    insert_decision_canary_block,
    strict_json_schema,
)
from app.services.ohlcv_feature_engine_service import build_multi_timeframe_feature_packet
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


CONTRACT = "v2-production-cutover-preflight-v1"
TEST_NAMESPACE = "V2_ACCEPTED_PRODUCTION_PREFLIGHT_TEST_ONLY"


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


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


async def _context(
    packet_path: Path,
    *,
    claim_id: str,
) -> AcceptedV2ProductionContext:
    packet = _read_json(packet_path)
    stocks = [row for row in packet.get("stocks") or () if isinstance(row, Mapping)]
    settings = get_settings()
    api_key = settings.action_api_key or settings.ohlcv_api_key or ""
    if not api_key:
        raise ValueError("preflight_ohlcv_api_key_missing")
    timeout = httpx.Timeout(settings.ohlcv_timeout_seconds, connect=10.0)
    payloads: dict[str, dict[str, object]] = {}
    async with httpx.AsyncClient(timeout=timeout) as client:
        for stock in stocks:
            ticker = str(stock.get("ticker") or "").upper()
            payloads[ticker] = await _fetch_ohlcv(
                client,
                ticker=ticker,
                base_url=settings.ohlcv_base_url,
                api_key=api_key,
            )
    cutoff = date.fromisoformat(str(packet.get("assessment_date") or "")[:10])
    evidence_packets: list[DecisionEvidencePacket] = []
    for stock in stocks:
        ticker = str(stock.get("ticker") or "").upper()
        periods = payloads[ticker]["periods"]
        assert isinstance(periods, Mapping)
        features = build_multi_timeframe_feature_packet(
            ticker=ticker,
            periods={
                str(key): value
                for key, value in periods.items()
                if isinstance(value, list)
            },
            cutoff=cutoff,
        )
        evidence_packets.append(
            build_decision_evidence_packet(
                packet=packet,
                stock=stock,
                technical_features=features,
            )
        )
    return build_accepted_v2_production_context(
        packet=packet,
        claim_id=claim_id,
        evidence_packets=evidence_packets,
    )


def _codex_batch(
    context: AcceptedV2ProductionContext,
    *,
    output_dir: Path,
    timeout: int,
) -> AcceptedV2ProductionBatchOutput:
    codex_bin = shutil.which("codex") or str(
        Path("/Applications/ChatGPT.app/Contents/Resources/codex")
    )
    schema = output_dir / "output.schema.json"
    _write_json(
        schema,
        strict_json_schema(AcceptedV2ProductionBatchOutput.model_json_schema()),
    )
    candidates = []
    adjudications = []
    for index in range(0, len(context.selected_subjects), 5):
        subjects = context.selected_subjects[index : index + 5]
        batch_number = index // 5 + 1
        prompt = output_dir / f"batch-{batch_number:02d}.prompt.txt"
        output = output_dir / f"batch-{batch_number:02d}.output.json"
        log = output_dir / f"batch-{batch_number:02d}.log"
        _write_text(prompt, accepted_v2_production_prompt(context, subjects=subjects))
        command = [
            codex_bin,
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "-m",
            REASONING_MODEL,
            "-c",
            f'model_reasoning_effort="{REASONING_EFFORT}"',
            "--output-schema",
            str(schema),
            "-o",
            str(output),
            "-",
        ]
        with prompt.open(encoding="utf-8") as stdin, log.open(
            "w", encoding="utf-8"
        ) as stdout:
            process = subprocess.run(
                command,
                cwd=output_dir,
                env=dict(os.environ),
                stdin=stdin,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
                text=True,
            )
        if process.returncode != 0:
            raise ValueError(f"preflight_codex_batch_failed:{batch_number}")
        batch = AcceptedV2ProductionBatchOutput.model_validate(_read_json(output))
        if {row.ticker for row in batch.candidates} != set(subjects):
            raise ValueError(f"preflight_batch_scope_mismatch:{batch_number}")
        candidates.extend(batch.candidates)
        adjudications.extend(batch.adjudications)
    return AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        candidates=tuple(candidates),
        adjudications=tuple(adjudications),
    )


def _production_payloads(
    artifacts: Sequence[object],
    deterministic_paths: Sequence[Path],
) -> list[dict[str, object]]:
    deterministic: dict[str, Mapping[str, object]] = {}
    for path in deterministic_paths:
        for row in _read_json(path).get("messages") or ():
            if isinstance(row, Mapping) and isinstance(row.get("payload"), Mapping):
                deterministic[str(row.get("ticker") or "")] = row["payload"]
    messages: list[dict[str, object]] = []
    for artifact in artifacts:
        blocks = getattr(artifact, "blocks")
        for block in blocks:
            payload = deterministic.get(block.ticker)
            if payload is None:
                raise ValueError(f"preflight_deterministic_payload_missing:{block.ticker}")
            base = str(payload.get("text") or "")
            text = insert_decision_canary_block(base, block.text)
            if len(text) > get_settings().telegram_message_max_chars:
                raise ValueError(f"preflight_message_too_long:{block.ticker}")
            messages.append(
                {
                    "ticker": block.ticker,
                    "route": "V2_ACCEPTED",
                    "text": text,
                    "logical_identity": (
                        f"{TEST_NAMESPACE}:{getattr(artifact, 'packet_id')}:{block.ticker}"
                    ),
                    "base_sha256": _sha256_text(base),
                    "rendered_sha256": _sha256_text(text),
                    "accepted_decision_id": block.accepted_decision_id,
                }
            )
    if len(messages) != len({str(row["ticker"]) for row in messages}):
        raise ValueError("preflight_duplicate_subject")
    return messages


async def _run(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    contexts = []
    artifacts = []
    for market, packet_path in (("kr", args.kr_packet), ("us", args.us_packet)):
        market_dir = args.output_dir / market
        context = await _context(packet_path, claim_id=f"preflight-{market}-20260830")
        _write_json(market_dir / "context.json", context.model_dump(mode="json"))
        output = _codex_batch(context, output_dir=market_dir, timeout=args.timeout)
        _write_json(market_dir / "candidate-output.json", output.model_dump(mode="json"))
        artifact = validate_accepted_v2_production_output(context, output)
        _write_json(market_dir / "accepted-artifact.json", artifact.model_dump(mode="json"))
        contexts.append(context)
        artifacts.append(artifact)
    messages = _production_payloads(
        artifacts,
        (args.kr_deterministic, args.us_deterministic),
    )
    _write_json(args.output_dir / "production-payloads.json", {"messages": messages})
    receipt = None
    sink = audit_test_sink(load_env_values(args.env_file))
    if args.send_test_sink:
        if not sink.get("available"):
            raise ValueError("dedicated_test_sink_unavailable")
        values = load_env_values(args.env_file)
        receipt = await deliver_test_messages(
            messages,
            token=values.get("TELEGRAM_BOT_TOKEN", ""),
            test_chat_id=values.get(str(sink["selected_test_key_name"]), ""),
            production_chat_id=values.get("TELEGRAM_CHAT_ID", ""),
            test_sink_alias=str(sink["test_sink_alias"]),
            production_sink_alias=str(sink["production_sink_alias"]),
            receipt_path=args.output_dir / "test-sink-receipt.json",
            contract="v2-production-premerge-test-sink-v1",
            namespace=TEST_NAMESPACE,
        )
    summary = {
        "contract": CONTRACT,
        "status": "PASS",
        "markets": {
            context.market: {
                "packet_id": context.packet_id,
                "subject_count": len(context.selected_subjects),
                "ready_count": artifact.ready_count,
                "not_ready_count": artifact.not_ready_count,
                "message_quality": artifact.message_quality,
            }
            for context, artifact in zip(contexts, artifacts, strict=True)
        },
        "subject_count": len(messages),
        "test_sink": sink,
        "test_sink_sent": bool(receipt),
        "test_sink_exact_payload": receipt.get("status") if receipt else "NOT_SENT",
        "production_recipient_send": 0,
        "production_delivery_intent_created": 0,
        "reasoning_model": REASONING_MODEL,
        "reasoning_effort": REASONING_EFFORT,
    }
    _write_json(args.output_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kr-packet", type=Path, required=True)
    parser.add_argument("--us-packet", type=Path, required=True)
    parser.add_argument("--kr-deterministic", type=Path, required=True)
    parser.add_argument("--us-deterministic", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--send-test-sink", action="store_true")
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
