from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
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
from app.services.codex_runtime_state_service import (
    RUNTIME_STATE_NOT_READY,
    CodexRuntimeStateError,
    prepare_codex_runtime_state,
)
from app.services.codex_network_transport_service import (
    NETWORK_READINESS_CONTRACT,
    CodexTransportError,
    classify_codex_transport_failure,
    probe_codex_network_readiness,
    retryable_codex_transport_failure,
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
V2_TRANSPORT_ATTEMPT_LIMIT = 2
V2_TRANSPORT_BACKOFF_SECONDS = 2.0

logger = logging.getLogger(__name__)
V2_STAGE_RECEIPT_CONTRACT = "accepted-v2-generation-stage-v1"


class V2CLIPathPreconditionError(ValueError):
    """Raised before Codex starts when a local invocation path is invalid."""


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


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _repository_path(path: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (_repository_root() / path).resolve()


def _root() -> Path:
    return _repository_path(Path(get_settings().data_dir)) / "ai_review"


def _runtime_state_root() -> Path:
    return _root().parent / "codex_runtime_state" / "v2"


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
    state_namespace: str,
) -> dict[str, object]:
    invocation_paths = {
        "cwd": _repository_path(cwd),
        "prompt": _repository_path(prompt),
        "output": _repository_path(output),
        "log": _repository_path(log),
        "schema": _repository_path(schema),
    }
    invocation_paths["output"].parent.mkdir(parents=True, exist_ok=True)
    invocation_paths["log"].parent.mkdir(parents=True, exist_ok=True)
    checks = {
        "cwd_is_absolute": invocation_paths["cwd"].is_absolute(),
        "cwd_exists": invocation_paths["cwd"].is_dir(),
        "schema_is_absolute": invocation_paths["schema"].is_absolute(),
        "schema_exists": invocation_paths["schema"].is_file(),
        "prompt_exists": invocation_paths["prompt"].is_file(),
        "output_parent_exists": invocation_paths["output"].parent.is_dir(),
        "log_parent_exists": invocation_paths["log"].parent.is_dir(),
    }
    logger.info(
        "v2_codex_cli_path_preflight %s",
        " ".join(f"{key}={str(value).lower()}" for key, value in checks.items()),
    )
    if not all(checks.values()):
        failed = ",".join(key for key, value in checks.items() if not value)
        raise V2CLIPathPreconditionError(f"v2_cli_path_precondition_failed:{failed}")

    runtime_state = prepare_codex_runtime_state(
        _runtime_state_root(),
        namespace=state_namespace,
    )
    logger.info(
        "v2_codex_runtime_state_preflight contract=%s namespace_hash=%s "
        "ownership=%s mode=%s sqlite_wal_probe=%s auth_reference=%s",
        runtime_state.contract,
        runtime_state.namespace_hash,
        runtime_state.ownership,
        runtime_state.mode,
        runtime_state.sqlite_wal_probe,
        runtime_state.signed_in_auth_reference,
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
        str(invocation_paths["schema"]),
        "-o",
        str(invocation_paths["output"]),
        "-",
    ]
    invocation_paths["log"].unlink(missing_ok=True)
    deadline = time.monotonic() + timeout
    total_network_probe_attempts = 0
    for transport_attempt in range(1, V2_TRANSPORT_ATTEMPT_LIMIT + 1):
        readiness = probe_codex_network_readiness()
        total_network_probe_attempts += readiness.attempts
        logger.info(
            "v2_codex_network_preflight contract=%s ready=%s attempts=%s "
            "resolved_address_count=%s failure_type=%s",
            readiness.contract,
            str(readiness.ready).lower(),
            readiness.attempts,
            readiness.resolved_address_count,
            readiness.failure_type.value if readiness.failure_type else "none",
        )
        if not readiness.ready:
            assert readiness.failure_type is not None
            raise CodexTransportError(
                readiness.failure_type,
                attempts=total_network_probe_attempts,
            )

        remaining_timeout = int(deadline - time.monotonic())
        if remaining_timeout < 1:
            raise CodexTransportError(
                classify_codex_transport_failure("", timed_out=True),
                attempts=transport_attempt,
            )
        invocation_paths["output"].unlink(missing_ok=True)
        attempt_log = invocation_paths["log"].with_name(
            f"{invocation_paths['log'].name}.attempt-{transport_attempt:02d}.tmp"
        )
        timed_out = False
        try:
            with (
                invocation_paths["prompt"].open(encoding="utf-8") as stdin,
                attempt_log.open("w", encoding="utf-8") as stdout,
            ):
                process = subprocess.run(
                    command,
                    cwd=invocation_paths["cwd"],
                    env=runtime_state.environment(),
                    stdin=stdin,
                    stdout=stdout,
                    stderr=subprocess.STDOUT,
                    timeout=remaining_timeout,
                    check=False,
                    text=True,
                )
        except subprocess.TimeoutExpired:
            timed_out = True
            process = None

        try:
            log_text = attempt_log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            log_text = ""
        with invocation_paths["log"].open("a", encoding="utf-8") as combined_log:
            combined_log.write(
                f"\n--- codex transport attempt {transport_attempt}/"
                f"{V2_TRANSPORT_ATTEMPT_LIMIT} ---\n"
            )
            combined_log.write(log_text)
        attempt_log.unlink(missing_ok=True)

        if (
            not timed_out
            and process is not None
            and process.returncode == 0
            and invocation_paths["output"].exists()
            and invocation_paths["output"].stat().st_size
        ):
            return {
                "contract": NETWORK_READINESS_CONTRACT,
                "network_probe_attempts": total_network_probe_attempts,
                "transport_attempts": transport_attempt,
                "retry_recovered": transport_attempt > 1,
            }

        if any(
            marker in log_text.casefold()
            for marker in (
                "readonly database",
                "failed to open state db",
                "failed to initialize in-process app-server client",
            )
        ):
            raise CodexRuntimeStateError(
                f"{RUNTIME_STATE_NOT_READY}:codex_app_server_initialization_failed"
            )

        failure_type = classify_codex_transport_failure(
            log_text,
            timed_out=timed_out,
        )
        can_retry = (
            retryable_codex_transport_failure(failure_type)
            and transport_attempt < V2_TRANSPORT_ATTEMPT_LIMIT
            and deadline - time.monotonic() > V2_TRANSPORT_BACKOFF_SECONDS + 1
        )
        if can_retry:
            logger.warning(
                "v2_codex_transport_retry failure_type=%s attempt=%s max_attempts=%s",
                failure_type.value,
                transport_attempt,
                V2_TRANSPORT_ATTEMPT_LIMIT,
            )
            time.sleep(V2_TRANSPORT_BACKOFF_SECONDS)
            continue
        raise CodexTransportError(failure_type, attempts=transport_attempt)

    raise CodexTransportError(
        classify_codex_transport_failure(""),
        attempts=V2_TRANSPORT_ATTEMPT_LIMIT,
    )


def _claim(packet_id: str, claim_id: str) -> dict[str, object]:
    value = _read_json(_root() / "claims" / f"{packet_id}.json")
    if value.get("packet_id") != packet_id or value.get("claim_id") != claim_id:
        raise ValueError("v2_production_stale_claim")
    return value


def _paths(claim: Mapping[str, object], claim_id: str) -> dict[str, Path]:
    final_review = Path(str(claim.get("final_output_path") or ""))
    if not final_review.name:
        raise ValueError("v2_production_final_review_path_missing")
    return accepted_v2_production_paths(
        _repository_path(final_review),
        claim_id=claim_id,
    )


def _stage_receipt_path(paths: Mapping[str, Path]) -> Path:
    return paths["receipt"].with_name(
        paths["receipt"].name.replace(".decision-v2-receipt.json", ".decision-v2-stage.json")
    )


def _record_stage(
    packet_id: str,
    claim_id: str,
    *,
    stage: str,
    batch_number: int | None = None,
    subject_count: int | None = None,
    reason: str | None = None,
) -> None:
    try:
        claim = _claim(packet_id, claim_id)
        paths = _paths(claim, claim_id)
        path = _stage_receipt_path(paths)
        receipt = _read_json(path) if path.exists() else {
            "contract": V2_STAGE_RECEIPT_CONTRACT,
            "packet_id": packet_id,
            "claim_id": claim_id,
            "stages": [],
        }
        stages = receipt.setdefault("stages", [])
        if isinstance(stages, list):
            stages.append(
                {
                    "stage": stage,
                    "batch_number": batch_number,
                    "subject_count": subject_count,
                    "reason": reason,
                    "recorded_at": datetime.now(UTC).isoformat(),
                }
            )
        _atomic_json(path, receipt)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return


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
    packet = _read_json(_repository_path(Path(str(claim.get("packet_path") or ""))))
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
    _record_stage(
        packet_id,
        claim_id,
        stage="context_ready",
        subject_count=len(context.selected_subjects),
    )
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
    packet = _read_json(_repository_path(Path(str(claim.get("packet_path") or ""))))
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
    _record_stage(packet_id, claim_id, stage="model_path_ready")
    claim = _claim(packet_id, claim_id)
    paths = _paths(claim, claim_id)
    context = AcceptedV2ProductionContext.model_validate(_read_json(paths["context"]))
    candidates = []
    adjudications = []
    batch_schema_repair_count = 0
    candidate_repair_count = 0
    transport_telemetry: list[dict[str, object]] = []
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
        _record_stage(
            packet_id,
            claim_id,
            stage="model_invoking",
            batch_number=batch_number,
            subject_count=len(subjects),
        )
        transport_telemetry.append(
            _invoke_signed_in_codex(
                codex_bin=codex_bin,
                prompt=batch_prompt,
                output=batch_output,
                log=batch_log,
                schema=Path(str(prepared["schema_path"])),
                cwd=paths["prompt"].parent,
                timeout=timeout,
                state_namespace=claim_id,
            )
        )
        raw_batch = _read_json(batch_output)
        _record_stage(
            packet_id,
            claim_id,
            stage="candidate_batch_created",
            batch_number=batch_number,
            subject_count=len(subjects),
        )
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
            transport_telemetry.append(
                _invoke_signed_in_codex(
                    codex_bin=codex_bin,
                    prompt=schema_repair_prompt,
                    output=schema_repair_output,
                    log=schema_repair_log,
                    schema=Path(str(prepared["schema_path"])),
                    cwd=paths["prompt"].parent,
                    timeout=timeout,
                    state_namespace=claim_id,
                )
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
            transport_telemetry.append(
                _invoke_signed_in_codex(
                    codex_bin=codex_bin,
                    prompt=repair_prompt,
                    output=repair_output,
                    log=repair_log,
                    schema=Path(str(prepared["schema_path"])),
                    cwd=paths["prompt"].parent,
                    timeout=timeout,
                    state_namespace=claim_id,
                )
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
    _record_stage(
        packet_id,
        claim_id,
        stage="accepted_artifact_created",
        subject_count=len(context.selected_subjects),
    )
    receipt["batch_schema_repair_count"] = batch_schema_repair_count
    receipt["candidate_repair_count"] = candidate_repair_count
    receipt["network_readiness_contract"] = NETWORK_READINESS_CONTRACT
    receipt["network_probe_attempts"] = sum(
        int(row["network_probe_attempts"]) for row in transport_telemetry
    )
    receipt["codex_transport_attempts"] = sum(
        int(row["transport_attempts"]) for row in transport_telemetry
    )
    receipt["transport_retry_recovered_count"] = sum(
        bool(row["retry_recovered"]) for row in transport_telemetry
    )
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
        CodexRuntimeStateError,
        FileNotFoundError,
        ValueError,
        json.JSONDecodeError,
        subprocess.TimeoutExpired,
    ) as exc:
        reason = (
            str(exc)
            if isinstance(exc, (CodexRuntimeStateError, CodexTransportError))
            else type(exc).__name__
        )
        result = _safe_suppression_receipt(
            args.packet_id,
            args.claim_id,
            reason=reason,
        )
        _record_stage(
            args.packet_id,
            args.claim_id,
            stage="suppressed_safe",
            reason=reason,
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
