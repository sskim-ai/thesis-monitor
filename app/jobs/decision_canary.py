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
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    build_decision_evidence_packet,
)
from app.services.decision_canary_service import (
    CANARY_REASONING_EFFORT,
    CANARY_REASONING_MODEL,
    RECEIPT_CONTRACT,
    DecisionCanaryBatchOutput,
    DecisionCanaryContext,
    build_decision_canary_context,
    configured_decision_canary_subjects,
    decision_canary_armed,
    decision_canary_paths,
    decision_canary_prompt,
    load_decision_canary_state,
    strict_json_schema,
    validate_decision_canary_output,
)
from app.services.ohlcv_feature_engine_service import (
    build_multi_timeframe_feature_packet,
)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
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
        raise ValueError("decision_canary_stale_claim")
    return value


def _paths(claim: Mapping[str, object], claim_id: str) -> dict[str, Path]:
    final_review = Path(str(claim.get("final_output_path") or ""))
    if not final_review.name:
        raise ValueError("decision_canary_final_review_path_missing")
    return decision_canary_paths(final_review, claim_id=claim_id)


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
        raise ValueError(f"invalid_decision_canary_ohlcv:{ticker}")
    return value


async def prepare_context(packet_id: str, claim_id: str) -> dict[str, object]:
    if not decision_canary_armed():
        return {"status": "NOT_ACTIVE", "packet_id": packet_id}
    claim = _claim(packet_id, claim_id)
    packet_path = Path(str(claim.get("packet_path") or ""))
    packet = _read_json(packet_path)
    market = str(packet.get("market") or "")
    if market not in {"kr", "us"}:
        raise ValueError("decision_canary_market_invalid")
    subjects = configured_decision_canary_subjects(market)  # type: ignore[arg-type]
    stocks = {
        str(row.get("ticker") or "").upper(): row
        for row in packet.get("stocks") or ()
        if isinstance(row, Mapping)
    }
    missing = [ticker for ticker in subjects if ticker not in stocks]
    if missing:
        raise ValueError("decision_canary_subject_unavailable:" + ",".join(missing))
    settings = get_settings()
    api_key = settings.action_api_key or settings.ohlcv_api_key or ""
    if not api_key:
        raise ValueError("decision_canary_ohlcv_api_key_missing")
    timeout = httpx.Timeout(settings.ohlcv_timeout_seconds, connect=10.0)
    payloads: dict[str, dict[str, object]] = {}
    async with httpx.AsyncClient(timeout=timeout) as client:
        for ticker in subjects:
            payloads[ticker] = await _fetch_ohlcv(
                client,
                ticker=ticker,
                base_url=settings.ohlcv_base_url,
                api_key=api_key,
            )
    cutoff = date.fromisoformat(str(packet.get("assessment_date") or "")[:10])
    evidence_packets: list[DecisionEvidencePacket] = []
    for ticker in subjects:
        raw_periods = payloads[ticker]["periods"]
        assert isinstance(raw_periods, Mapping)
        features = build_multi_timeframe_feature_packet(
            ticker=ticker,
            periods={
                str(key): value for key, value in raw_periods.items() if isinstance(value, list)
            },
            cutoff=cutoff,
        )
        evidence_packets.append(
            build_decision_evidence_packet(
                packet=packet,
                stock=stocks[ticker],
                technical_features=features,
            )
        )
    continuity_state = load_decision_canary_state()
    continuity_candidates = {
        row.ticker: row.candidate
        for row in (continuity_state.entries if continuity_state is not None else ())
        if row.market == market
    }
    context = build_decision_canary_context(
        packet=packet,
        claim_id=claim_id,
        evidence_packets=evidence_packets,
        continuity_candidates=continuity_candidates,
    )
    paths = _paths(claim, claim_id)
    _atomic_json(paths["context"], context.model_dump(mode="json"))
    _atomic_json(
        paths["schema"],
        strict_json_schema(DecisionCanaryBatchOutput.model_json_schema()),
    )
    _atomic_text(paths["prompt"], decision_canary_prompt(context))
    return {
        "status": "CONTEXT_READY",
        "packet_id": packet_id,
        "claim_id": claim_id,
        "market": market,
        "subjects": list(subjects),
        "context_path": str(paths["context"]),
        "prompt_path": str(paths["prompt"]),
        "schema_path": str(paths["schema"]),
        "temp_output_path": str(paths["temp"]),
        "final_output_path": str(paths["final"]),
    }


def validate_output(packet_id: str, claim_id: str) -> dict[str, object]:
    claim = _claim(packet_id, claim_id)
    paths = _paths(claim, claim_id)
    context = DecisionCanaryContext.model_validate(_read_json(paths["context"]))
    candidate = DecisionCanaryBatchOutput.model_validate(_read_json(paths["temp"]))
    artifact = validate_decision_canary_output(context, candidate)
    _atomic_json(paths["final"], artifact.model_dump(mode="json"))
    receipt = {
        "contract": RECEIPT_CONTRACT,
        "status": "PASS",
        "packet_id": packet_id,
        "claim_id": claim_id,
        "subjects": list(artifact.selected_subjects),
        "reasoning_model": artifact.reasoning_model,
        "reasoning_effort": artifact.reasoning_effort,
        "message_quality": artifact.message_quality,
        "production_send": 0,
        "validated_at": artifact.validated_at,
    }
    _atomic_json(paths["receipt"], receipt)
    return {
        "status": "PASS",
        "packet_id": packet_id,
        "claim_id": claim_id,
        "subjects": list(artifact.selected_subjects),
        "artifact_path": str(paths["final"]),
        "receipt_path": str(paths["receipt"]),
    }


def _safe_suppression_receipt(
    packet_id: str,
    claim_id: str,
    *,
    reason: str,
) -> dict[str, object]:
    try:
        paths = _paths(_claim(packet_id, claim_id), claim_id)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return {
            "status": "CANARY_DECISION_SUPPRESSED_SAFE",
            "packet_id": packet_id,
            "claim_id": claim_id,
            "reason": reason,
        }
    receipt = {
        "contract": RECEIPT_CONTRACT,
        "status": "CANARY_DECISION_SUPPRESSED_SAFE",
        "packet_id": packet_id,
        "claim_id": claim_id,
        "reason": reason,
        "rejected_decision_sent": 0,
        "fallback_eligibility_preserved": True,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    _atomic_json(paths["receipt"], receipt)
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
    prompt_path = Path(str(prepared["prompt_path"]))
    schema_path = Path(str(prepared["schema_path"]))
    output_path = Path(str(prepared["temp_output_path"]))
    claim = _claim(packet_id, claim_id)
    paths = _paths(claim, claim_id)
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
        CANARY_REASONING_MODEL,
        "-c",
        f'model_reasoning_effort="{CANARY_REASONING_EFFORT}"',
        "--output-schema",
        str(schema_path),
        "-o",
        str(output_path),
        "-",
    ]
    with (
        prompt_path.open(encoding="utf-8") as stdin,
        paths["log"].open("w", encoding="utf-8") as stdout,
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
    if process.returncode != 0 or not output_path.exists() or not output_path.stat().st_size:
        raise ValueError("signed_in_codex_cli_decision_generation_failed")
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
    parser = argparse.ArgumentParser(
        description="Generate a bounded current decision canary sidecar"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "validate", "generate"):
        child = subparsers.add_parser(name)
        child.add_argument("--packet-id", required=True)
        child.add_argument("--claim-id", required=True)
        if name == "generate":
            child.add_argument("--timeout", type=int, default=420)
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
