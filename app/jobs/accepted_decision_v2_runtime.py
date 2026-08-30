from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
from collections.abc import Mapping
from datetime import UTC, date, datetime
from pathlib import Path

import httpx

from app.config import get_settings
from app.services.accepted_decision_v2_runtime_service import (
    RECEIPT_CONTRACT,
    REASONING_EFFORT,
    REASONING_MODEL,
    AcceptedV2ProductionBatchOutput,
    AcceptedV2ProductionContext,
    accepted_v2_production_paths,
    accepted_v2_production_prompt,
    build_accepted_v2_production_context,
    load_accepted_v2_production_artifact,
    v2_accepted_production_armed,
    validate_accepted_v2_production_output,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    build_decision_evidence_packet,
)
from app.services.decision_canary_service import strict_json_schema
from app.services.ohlcv_feature_engine_service import build_multi_timeframe_feature_packet


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _root() -> Path:
    return Path(get_settings().data_dir) / "ai_review"


def _claim(packet_id: str, claim_id: str) -> dict[str, object]:
    value = _read_json(_root() / "claims" / f"{packet_id}.json")
    if value.get("packet_id") != packet_id or value.get("claim_id") != claim_id:
        raise ValueError("v2_production_stale_claim")
    return value


def _paths(claim: Mapping[str, object], claim_id: str) -> dict[str, Path]:
    final_review = Path(str(claim.get("final_output_path") or ""))
    if not final_review.name:
        raise ValueError("v2_production_final_review_path_missing")
    return accepted_v2_production_paths(final_review, claim_id=claim_id)


async def _fetch_ohlcv(
    client: httpx.AsyncClient,
    *,
    ticker: str,
    base_url: str,
    api_key: str,
) -> dict[str, object]:
    response = await client.get(
        f"{base_url.rstrip('/')}/ohlcv",
        params={
            "symbol": ticker,
            "periods": "daily,weekly,monthly",
            "count": 1000,
            "include_indicators": "false",
        },
        headers={"X-API-Key": api_key},
    )
    response.raise_for_status()
    value = response.json()
    if not isinstance(value, dict) or not isinstance(value.get("periods"), dict):
        raise ValueError(f"invalid_v2_production_ohlcv:{ticker}")
    return value


async def prepare_context(packet_id: str, claim_id: str) -> dict[str, object]:
    if not v2_accepted_production_armed():
        return {"status": "NOT_ACTIVE", "packet_id": packet_id}
    claim = _claim(packet_id, claim_id)
    packet = _read_json(Path(str(claim.get("packet_path") or "")))
    stocks = [row for row in packet.get("stocks") or () if isinstance(row, Mapping)]
    if not stocks:
        raise ValueError("v2_production_packet_stocks_missing")
    settings = get_settings()
    api_key = settings.action_api_key or settings.ohlcv_api_key or ""
    if not api_key:
        raise ValueError("v2_production_ohlcv_api_key_missing")
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
    context = build_accepted_v2_production_context(
        packet=packet,
        claim_id=claim_id,
        evidence_packets=evidence_packets,
    )
    paths = _paths(claim, claim_id)
    _atomic_json(paths["context"], context.model_dump(mode="json"))
    _atomic_json(
        paths["schema"],
        strict_json_schema(AcceptedV2ProductionBatchOutput.model_json_schema()),
    )
    _atomic_text(paths["prompt"], accepted_v2_production_prompt(context))
    return {
        "status": "CONTEXT_READY",
        "packet_id": packet_id,
        "claim_id": claim_id,
        "market": context.market,
        "subjects": list(context.selected_subjects),
        "context_path": str(paths["context"]),
        "prompt_path": str(paths["prompt"]),
        "schema_path": str(paths["schema"]),
        "temp_output_path": str(paths["temp"]),
        "final_output_path": str(paths["final"]),
    }


def validate_output(packet_id: str, claim_id: str) -> dict[str, object]:
    claim = _claim(packet_id, claim_id)
    paths = _paths(claim, claim_id)
    context = AcceptedV2ProductionContext.model_validate(_read_json(paths["context"]))
    output = AcceptedV2ProductionBatchOutput.model_validate(_read_json(paths["temp"]))
    artifact = validate_accepted_v2_production_output(context, output)
    _atomic_json(paths["final"], artifact.model_dump(mode="json"))
    packet = _read_json(Path(str(claim.get("packet_path") or "")))
    load_accepted_v2_production_artifact(
        paths["final"], packet=packet, claim_id=claim_id
    )
    receipt = {
        "contract": RECEIPT_CONTRACT,
        "status": artifact.status,
        "packet_id": packet_id,
        "claim_id": claim_id,
        "subjects": list(artifact.selected_subjects),
        "ready_count": artifact.ready_count,
        "not_ready_count": artifact.not_ready_count,
        "reasoning_model": artifact.reasoning_model,
        "reasoning_effort": artifact.reasoning_effort,
        "message_quality": artifact.message_quality,
        "raw_candidate_visible": 0,
        "production_send": 0,
        "validated_at": artifact.validated_at,
    }
    _atomic_json(paths["receipt"], receipt)
    return receipt


def _safe_suppression_receipt(
    packet_id: str,
    claim_id: str,
    *,
    reason: str,
) -> dict[str, object]:
    receipt = {
        "contract": RECEIPT_CONTRACT,
        "status": "V2_DECISION_SUPPRESSED_SAFE",
        "packet_id": packet_id,
        "claim_id": claim_id,
        "reason": reason,
        "raw_candidate_visible": 0,
        "rejected_decision_sent": 0,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    try:
        paths = _paths(_claim(packet_id, claim_id), claim_id)
        _atomic_json(paths["receipt"], receipt)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        pass
    return receipt


async def generate(packet_id: str, claim_id: str, *, timeout: int) -> dict[str, object]:
    prepared = await prepare_context(packet_id, claim_id)
    if prepared.get("status") != "CONTEXT_READY":
        return prepared
    codex_bin = shutil.which("codex") or str(
        Path("/Applications/ChatGPT.app/Contents/Resources/codex")
    )
    if not Path(codex_bin).exists():
        raise ValueError("signed_in_codex_cli_missing")
    claim = _claim(packet_id, claim_id)
    paths = _paths(claim, claim_id)
    context = AcceptedV2ProductionContext.model_validate(_read_json(paths["context"]))
    candidates = []
    adjudications = []
    for index in range(0, len(context.selected_subjects), 5):
        subjects = context.selected_subjects[index : index + 5]
        batch_number = index // 5 + 1
        batch_prompt = paths["prompt"].with_name(
            f"{paths['prompt'].stem}.batch-{batch_number:02d}.txt"
        )
        batch_output = paths["temp"].with_name(
            f"{paths['temp'].stem}.batch-{batch_number:02d}.json"
        )
        batch_log = paths["log"].with_name(
            f"{paths['log'].stem}.batch-{batch_number:02d}.log"
        )
        _atomic_text(
            batch_prompt,
            accepted_v2_production_prompt(context, subjects=subjects),
        )
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
            str(prepared["schema_path"]),
            "-o",
            str(batch_output),
            "-",
        ]
        with (
            batch_prompt.open(encoding="utf-8") as stdin,
            batch_log.open("w", encoding="utf-8") as stdout,
        ):
            process = subprocess.run(
                command,
                cwd=paths["prompt"].parent,
                env=dict(os.environ),
                stdin=stdin,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
                text=True,
            )
        if process.returncode != 0 or not batch_output.exists() or not batch_output.stat().st_size:
            raise ValueError("signed_in_codex_cli_v2_production_generation_failed")
        batch = AcceptedV2ProductionBatchOutput.model_validate(_read_json(batch_output))
        if (
            batch.packet_id != context.packet_id
            or batch.claim_id != context.claim_id
            or batch.market != context.market
            or batch.assessment_date != context.assessment_date
            or {row.ticker for row in batch.candidates} != set(subjects)
        ):
            raise ValueError("v2_production_batch_identity_or_scope_mismatch")
        candidates.extend(batch.candidates)
        adjudications.extend(batch.adjudications)
    output_path = Path(str(prepared["temp_output_path"]))
    _atomic_json(
        output_path,
        AcceptedV2ProductionBatchOutput(
            packet_id=context.packet_id,
            claim_id=context.claim_id,
            market=context.market,
            assessment_date=context.assessment_date,
            candidates=tuple(candidates),
            adjudications=tuple(adjudications),
        ).model_dump(mode="json"),
    )
    return validate_output(packet_id, claim_id)


async def _run(args: argparse.Namespace) -> None:
    try:
        if args.command == "prepare":
            result = await prepare_context(args.packet_id, args.claim_id)
        elif args.command == "validate":
            result = validate_output(args.packet_id, args.claim_id)
        else:
            result = await generate(args.packet_id, args.claim_id, timeout=args.timeout)
    except (
        FileNotFoundError,
        ValueError,
        json.JSONDecodeError,
        httpx.HTTPError,
        subprocess.TimeoutExpired,
    ) as exc:
        result = _safe_suppression_receipt(
            args.packet_id,
            args.claim_id,
            reason=type(exc).__name__,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "validate", "generate"))
    parser.add_argument("--packet-id", required=True)
    parser.add_argument("--claim-id", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
