from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2ProductionBatchOutput,
    AcceptedV2ProductionArtifact,
    AcceptedV2ProductionContext,
    REASONING_EFFORT,
    REASONING_MODEL,
    validate_accepted_v2_production_output,
)
from scripts.v2_production_cutover_preflight import _codex_batch, _context


CONTRACT = "packet-ai-consumability-v2-replay-v1"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def _run(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    context_path = args.output_dir / "context.json"
    output_path = args.output_dir / "candidate-output.json"
    artifact_path = args.output_dir / "accepted-artifact.json"
    if args.resume_existing:
        context = AcceptedV2ProductionContext.model_validate_json(
            context_path.read_text(encoding="utf-8")
        )
        output = AcceptedV2ProductionBatchOutput.model_validate_json(
            output_path.read_text(encoding="utf-8")
        )
        artifact = AcceptedV2ProductionArtifact.model_validate_json(
            artifact_path.read_text(encoding="utf-8")
        )
    else:
        context = await _context(args.packet, claim_id=args.claim_id)
        _write_json(context_path, context.model_dump(mode="json"))
        output = _codex_batch(
            context,
            output_dir=args.output_dir,
            timeout=args.timeout,
            state_namespace=args.state_namespace,
        )
        _write_json(output_path, output.model_dump(mode="json"))
        artifact = validate_accepted_v2_production_output(context, output)
        _write_json(artifact_path, artifact.model_dump(mode="json"))
    if context.market != "us" or len(context.selected_subjects) != 14:
        raise ValueError("run53_us_14_subject_context_required")
    decisions = [
        {
            "ticker": block.ticker,
            "decision": block.decision,
            "directional_balance": {
                "buy": block.buy_balance,
                "sell": block.sell_balance,
            },
            "accepted_decision_id": block.accepted_decision_id,
        }
        for block in artifact.blocks
    ]
    summary = {
        "contract": CONTRACT,
        "packet_id": context.packet_id,
        "source_packet_sha256": context.source_packet_sha256,
        "claim_id": context.claim_id,
        "namespace": args.state_namespace,
        "market": context.market,
        "reasoning_model": REASONING_MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "timeout_seconds": args.timeout,
        "context_ready_count": len(context.selected_subjects),
        "network_preflight_reached": True,
        "codex_app_server_reached": True,
        "model_reached": True,
        "candidate_count": len(output.candidates),
        "accepted_count": artifact.ready_count,
        "explicit_count": len(artifact.blocks),
        "fallback_count": 0,
        "message_quality": artifact.message_quality,
        "decisions": decisions,
        "accepted_artifact_sha256": _sha256(artifact_path),
        "production_send": 0,
        "production_state_mutation": 0,
    }
    _write_json(args.summary, summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--claim-id", default="packet-readiness-run53-test-only")
    parser.add_argument(
        "--state-namespace",
        default="PACKET_READINESS_REPAIR_20260903_RUN53_TEST_ONLY",
    )
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--resume-existing", action="store_true")
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
