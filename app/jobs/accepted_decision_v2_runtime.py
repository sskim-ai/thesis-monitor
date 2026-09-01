from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from app.config import get_settings
from app.services.accepted_decision_v2_runtime_service import (
    RECEIPT_CONTRACT,
    REASONING_EFFORT,
    REASONING_MODEL,
    AcceptedV2ProductionBatchOutput,
    AcceptedV2ProductionContext,
    accepted_v2_production_batch_schema_repair_prompt,
    accepted_v2_production_paths,
    accepted_v2_production_prompt,
    accepted_v2_production_repair_prompt,
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
from app.services.packet_owned_technical_context_service import (
    PacketOwnedTechnicalContext,
    packet_owned_context_for_stock,
)
from app.services.preconfirmation_decision_v2_service import (
    validate_preconfirmation_candidate,
)


V2_REASONING_BATCH_SIZE = 3
V2_BATCH_SCHEMA_REPAIR_LIMIT = 1


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


def _signed_in_codex_bin() -> str:
    candidates = (
        os.environ.get("CODEX_CLI_BIN"),
        "/Applications/ChatGPT.app/Contents/Resources/codex",
        shutil.which("codex"),
        "/Users/sskim/Applications/Codex.app/Contents/Resources/codex",
    )
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise ValueError("signed_in_codex_cli_missing")


def _invoke_signed_in_codex(
    *,
    codex_bin: str,
    prompt: Path,
    output: Path,
    log: Path,
    schema: Path,
    cwd: Path,
    timeout: int,
) -> None:
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
    with prompt.open(encoding="utf-8") as stdin, log.open("w", encoding="utf-8") as stdout:
        process = subprocess.run(
            command,
            cwd=cwd,
            env=dict(os.environ),
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
            text=True,
        )
    if process.returncode != 0 or not output.exists() or not output.stat().st_size:
        raise ValueError("signed_in_codex_cli_v2_production_generation_failed")


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


def _schema_validation_errors(exc: ValidationError) -> tuple[str, ...]:
    return tuple(
        ":".join(
            (
                ".".join(str(part) for part in error["loc"]),
                str(error["type"]),
                str(error["msg"]),
            )
        )
        for error in exc.errors()
    )


async def prepare_context(packet_id: str, claim_id: str) -> dict[str, object]:
    if not v2_accepted_production_armed():
        return {"status": "NOT_ACTIVE", "packet_id": packet_id}
    claim = _claim(packet_id, claim_id)
    packet = _read_json(Path(str(claim.get("packet_path") or "")))
    stocks = [row for row in packet.get("stocks") or () if isinstance(row, Mapping)]
    if not stocks:
        raise ValueError("v2_production_packet_stocks_missing")
    evidence_packets: list[DecisionEvidencePacket] = []
    technical_contexts: list[PacketOwnedTechnicalContext] = []
    for stock in stocks:
        technical_context = packet_owned_context_for_stock(packet=packet, stock=stock)
        technical_contexts.append(technical_context)
        evidence_packets.append(
            build_decision_evidence_packet(
                packet=packet,
                stock=stock,
                technical_context=technical_context,
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
        "technical_context_counts": {
            status: sum(row.status == status for row in technical_contexts)
            for status in ("FULL", "PARTIAL_SAFE", "UNAVAILABLE", "INVALID")
        },
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
    load_accepted_v2_production_artifact(paths["final"], packet=packet, claim_id=claim_id)
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
    codex_bin = _signed_in_codex_bin()
    claim = _claim(packet_id, claim_id)
    paths = _paths(claim, claim_id)
    context = AcceptedV2ProductionContext.model_validate(_read_json(paths["context"]))
    candidates = []
    adjudications = []
    batch_schema_repair_count = 0
    candidate_repair_count = 0
    for index in range(0, len(context.selected_subjects), V2_REASONING_BATCH_SIZE):
        subjects = context.selected_subjects[index : index + V2_REASONING_BATCH_SIZE]
        batch_number = index // V2_REASONING_BATCH_SIZE + 1
        batch_prompt = paths["prompt"].with_name(
            f"{paths['prompt'].stem}.batch-{batch_number:02d}.txt"
        )
        batch_output = paths["temp"].with_name(
            f"{paths['temp'].stem}.batch-{batch_number:02d}.json"
        )
        batch_log = paths["log"].with_name(f"{paths['log'].stem}.batch-{batch_number:02d}.log")
        _atomic_text(
            batch_prompt,
            accepted_v2_production_prompt(context, subjects=subjects),
        )
        _invoke_signed_in_codex(
            codex_bin=codex_bin,
            prompt=batch_prompt,
            output=batch_output,
            log=batch_log,
            schema=Path(str(prepared["schema_path"])),
            cwd=paths["prompt"].parent,
            timeout=timeout,
        )
        raw_batch = _read_json(batch_output)
        try:
            batch = AcceptedV2ProductionBatchOutput.model_validate(raw_batch)
        except ValidationError as exc:
            if V2_BATCH_SCHEMA_REPAIR_LIMIT != 1:
                raise
            schema_repair_prompt = paths["prompt"].with_name(
                f"{paths['prompt'].stem}.batch-{batch_number:02d}.schema-repair.txt"
            )
            schema_repair_output = paths["temp"].with_name(
                f"{paths['temp'].stem}.batch-{batch_number:02d}.schema-repair.json"
            )
            schema_repair_log = paths["log"].with_name(
                f"{paths['log'].stem}.batch-{batch_number:02d}.schema-repair.log"
            )
            _atomic_text(
                schema_repair_prompt,
                accepted_v2_production_batch_schema_repair_prompt(
                    context,
                    subjects=subjects,
                    rejected_output=raw_batch,
                    validation_errors=_schema_validation_errors(exc),
                ),
            )
            _invoke_signed_in_codex(
                codex_bin=codex_bin,
                prompt=schema_repair_prompt,
                output=schema_repair_output,
                log=schema_repair_log,
                schema=Path(str(prepared["schema_path"])),
                cwd=paths["prompt"].parent,
                timeout=timeout,
            )
            batch = AcceptedV2ProductionBatchOutput.model_validate(
                _read_json(schema_repair_output)
            )
            batch_schema_repair_count += 1
        if (
            batch.packet_id != context.packet_id
            or batch.claim_id != context.claim_id
            or batch.market != context.market
            or batch.assessment_date != context.assessment_date
            or {row.ticker for row in batch.candidates} != set(subjects)
        ):
            raise ValueError("v2_production_batch_identity_or_scope_mismatch")
        batch_candidates = {row.ticker: row for row in batch.candidates}
        batch_adjudications = {row.ticker: row for row in batch.adjudications}
        if len(batch_adjudications) != len(batch.adjudications):
            raise ValueError("v2_production_duplicate_batch_adjudication")
        packets = {row.ticker: row for row in context.evidence_packets}
        for ticker in subjects:
            validation = validate_preconfirmation_candidate(
                packets[ticker], batch_candidates[ticker]
            )
            if validation.valid:
                continue
            repair_prompt = paths["prompt"].with_name(
                f"{paths['prompt'].stem}.batch-{batch_number:02d}.{ticker}.repair.txt"
            )
            repair_output = paths["temp"].with_name(
                f"{paths['temp'].stem}.batch-{batch_number:02d}.{ticker}.repair.json"
            )
            repair_log = paths["log"].with_name(
                f"{paths['log'].stem}.batch-{batch_number:02d}.{ticker}.repair.log"
            )
            _atomic_text(
                repair_prompt,
                accepted_v2_production_repair_prompt(
                    context,
                    ticker=ticker,
                    rejected_candidate=batch_candidates[ticker],
                    validation_errors=tuple(dict.fromkeys(validation.errors)),
                ),
            )
            _invoke_signed_in_codex(
                codex_bin=codex_bin,
                prompt=repair_prompt,
                output=repair_output,
                log=repair_log,
                schema=Path(str(prepared["schema_path"])),
                cwd=paths["prompt"].parent,
                timeout=timeout,
            )
            repaired = AcceptedV2ProductionBatchOutput.model_validate(_read_json(repair_output))
            if (
                repaired.packet_id != context.packet_id
                or repaired.claim_id != context.claim_id
                or repaired.market != context.market
                or repaired.assessment_date != context.assessment_date
                or len(repaired.candidates) != 1
                or repaired.candidates[0].ticker != ticker
                or any(row.ticker != ticker for row in repaired.adjudications)
            ):
                raise ValueError("v2_production_repair_identity_or_scope_mismatch")
            repaired_validation = validate_preconfirmation_candidate(
                packets[ticker], repaired.candidates[0]
            )
            if not repaired_validation.valid:
                raise ValueError(
                    "v2_production_bounded_repair_failed:"
                    + ticker
                    + ":"
                    + ",".join(repaired_validation.errors)
                )
            batch_candidates[ticker] = repaired.candidates[0]
            candidate_repair_count += 1
            batch_adjudications.pop(ticker, None)
            batch_adjudications.update({row.ticker: row for row in repaired.adjudications})
        candidates.extend(batch_candidates[ticker] for ticker in subjects)
        adjudications.extend(
            batch_adjudications[ticker] for ticker in subjects if ticker in batch_adjudications
        )
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
    receipt = validate_output(packet_id, claim_id)
    receipt["batch_schema_repair_count"] = batch_schema_repair_count
    receipt["candidate_repair_count"] = candidate_repair_count
    _atomic_json(paths["receipt"], receipt)
    return receipt


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
