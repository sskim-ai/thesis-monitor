from __future__ import annotations

import asyncio
import json
import signal
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.jobs import accepted_decision_v2_runtime as runtime
from app.jobs import stock_decision
from app.services.codex_network_transport_service import (
    NETWORK_READINESS_CONTRACT,
    CodexNetworkReadiness,
    CodexTransportError,
    CodexTransportFailureType,
)
from app.services.v2_natural_proof_service import (
    ExplicitV2NaturalProofCounts,
    evaluate_explicit_v2_natural_proof,
)


def _runtime_claim(tmp_path: Path) -> tuple[str, str, dict[str, object]]:
    packet_id = "2026-09-04-kr-run-test"
    claim_id = "claim-generation-2"
    packet_path = tmp_path / "data/ai_review/inbox" / f"{packet_id}.json"
    packet_path.parent.mkdir(parents=True)
    packet_path.write_text(
        json.dumps(
            {
                "packet_id": packet_id,
                "market": "kr",
                "assessment_date": "2026-09-04",
                "source_monitor_run_id": "56",
            }
        ),
        encoding="utf-8",
    )
    claim = {
        "packet_id": packet_id,
        "claim_id": claim_id,
        "market": "kr",
        "owner": "primary",
        "fencing_token": claim_id,
        "claim_generation": 2,
        "packet_path": str(packet_path.relative_to(tmp_path)),
        "final_output_path": (
            f"data/ai_review/outbox/{packet_id}--daily-review-v3.json"
        ),
    }
    claim_path = tmp_path / "data/ai_review/claims" / f"{packet_id}.json"
    claim_path.parent.mkdir(parents=True)
    claim_path.write_text(json.dumps(claim), encoding="utf-8")
    return packet_id, claim_id, claim


@pytest.fixture(autouse=True)
def _runtime_dependencies(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(runtime, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(runtime, "_root", lambda: tmp_path / "data/ai_review")
    monkeypatch.setattr(
        runtime,
        "probe_codex_network_readiness",
        lambda: CodexNetworkReadiness(
            contract=NETWORK_READINESS_CONTRACT,
            ready=True,
            host="chatgpt.com",
            port=443,
            attempts=1,
            resolved_address_count=1,
        ),
    )


def test_command_deadline_remains_active_after_forensic_168_second_boundary() -> None:
    deadline = runtime.V2CommandDeadline(started_at=1000.0, timeout_seconds=1800)

    assert deadline.remaining_seconds(now=1168.3) == 1632
    assert deadline.remaining_seconds(now=2799.9) == 1
    assert deadline.remaining_seconds(now=2800.0) == 0


def test_signal_terminated_child_is_interruption_not_transport_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    claims = tmp_path / "data/ai_review/claims"
    claims.mkdir(parents=True)
    prompt = claims / "prompt.txt"
    schema = claims / "schema.json"
    prompt.write_text("prompt", encoding="utf-8")
    schema.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        runtime.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=128 + signal.SIGINT),
    )

    with pytest.raises(runtime.V2GenerationInterrupted) as error:
        runtime._invoke_signed_in_codex(
            codex_bin="/bin/echo",
            prompt=prompt,
            output=claims / "output.json",
            log=claims / "log.txt",
            schema=schema,
            cwd=claims,
            timeout=1800,
            state_namespace="signal-test",
        )

    assert error.value.reason == runtime.V2InterruptionReason.AUTHORIZED_CANCEL


def test_interruption_persists_claim_bound_terminal_receipt_and_stage(
    tmp_path: Path,
) -> None:
    packet_id, claim_id, claim = _runtime_claim(tmp_path)

    receipt = runtime._terminal_suppression_receipt(
        packet_id,
        claim_id,
        claim=claim,
        reason=runtime.V2InterruptionReason.AUTHORIZED_CANCEL.value,
        terminal_state="INTERRUPTED",
        interruption_reason=runtime.V2InterruptionReason.AUTHORIZED_CANCEL,
    )
    paths = runtime._paths(claim, claim_id)
    persisted = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    stage_path = runtime._stage_receipt_path(paths)
    stage = json.loads(stage_path.read_text(encoding="utf-8"))

    assert receipt == persisted
    assert persisted["generation_id"].endswith(f":{claim_id}:2")
    assert persisted["fencing_token"] == claim_id
    assert persisted["terminal_state"] == "INTERRUPTED"
    assert persisted["interruption_reason"] == "AUTHORIZED_CANCEL"
    assert persisted["accepted"] is False
    assert persisted["delivery_eligible"] is False
    assert persisted["compatibility_fallback_eligible"] is True
    assert stage["terminal_state"] == "INTERRUPTED"
    assert stage["latest_stage"] == "interrupted"


def test_cross_generation_stage_receipt_is_not_reused(tmp_path: Path) -> None:
    packet_id, claim_id, claim = _runtime_claim(tmp_path)
    paths = runtime._paths(claim, claim_id)
    stage_path = runtime._stage_receipt_path(paths)
    stage_path.parent.mkdir(parents=True, exist_ok=True)
    stage_path.write_text(
        json.dumps(
            {
                "contract": runtime.V2_STAGE_RECEIPT_CONTRACT,
                "packet_id": packet_id,
                "claim_id": claim_id,
                "generation_id": "other-generation",
                "market": "kr",
                "business_date": "2026-09-04",
                "run_id": "56",
                "claim_owner": "primary",
                "fencing_token": claim_id,
                "claim_generation": 1,
                "terminal_state": "ACTIVE",
                "stages": [],
            }
        ),
        encoding="utf-8",
    )

    runtime._record_stage(
        packet_id,
        claim_id,
        stage="model_invoking",
        claim_snapshot=claim,
    )

    persisted = json.loads(stage_path.read_text(encoding="utf-8"))
    assert persisted["generation_id"] == "other-generation"
    assert persisted["stages"] == []


def test_late_suppression_cannot_replace_claim_bound_accepted_artifact(
    tmp_path: Path,
) -> None:
    packet_id, claim_id, claim = _runtime_claim(tmp_path)
    paths = runtime._paths(claim, claim_id)
    paths["final"].parent.mkdir(parents=True, exist_ok=True)
    paths["final"].write_text(
        json.dumps(
            {
                "status": "PASS",
                "packet_id": packet_id,
                "claim_id": claim_id,
            }
        ),
        encoding="utf-8",
    )

    receipt = runtime._terminal_suppression_receipt(
        packet_id,
        claim_id,
        claim=claim,
        reason="late_timeout",
        terminal_state="TIMED_OUT",
        interruption_reason=runtime.V2InterruptionReason.COMMAND_TIMEOUT,
    )

    assert receipt["status"] == "PASS"
    assert receipt["terminal_state"] == "ACCEPTED"
    assert receipt["accepted_artifact_preserved"] is True


def test_generate_converts_command_timeout_to_terminal_receipt(
    monkeypatch,
    tmp_path: Path,
) -> None:
    packet_id, claim_id, _claim = _runtime_claim(tmp_path)

    class Heartbeat:
        renewal_count = 3
        ownership_lost = False

        def __init__(self, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "Heartbeat":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    async def timeout(*args: object, **kwargs: object) -> dict[str, object]:
        raise CodexTransportError(CodexTransportFailureType.MODEL_TIMEOUT, attempts=1)

    monkeypatch.setattr(runtime, "_ClaimLeaseHeartbeat", Heartbeat)
    monkeypatch.setattr(runtime, "_generate_claim_owned", timeout)

    receipt = asyncio.run(runtime.generate(packet_id, claim_id, timeout=1800))

    assert receipt["status"] == "V2_DECISION_SUPPRESSED_SAFE"
    assert receipt["terminal_state"] == "TIMED_OUT"
    assert receipt["interruption_reason"] == "COMMAND_TIMEOUT"
    assert receipt["claim_lease_renewal_count"] == 3


def test_generate_converts_task_cancellation_to_terminal_receipt(
    monkeypatch,
    tmp_path: Path,
) -> None:
    packet_id, claim_id, _claim = _runtime_claim(tmp_path)

    class Heartbeat:
        renewal_count = 1
        ownership_lost = False

        def __init__(self, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "Heartbeat":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    async def cancel(*args: object, **kwargs: object) -> dict[str, object]:
        raise asyncio.CancelledError

    monkeypatch.setattr(runtime, "_ClaimLeaseHeartbeat", Heartbeat)
    monkeypatch.setattr(runtime, "_generate_claim_owned", cancel)

    receipt = asyncio.run(runtime.generate(packet_id, claim_id, timeout=1800))

    assert receipt["terminal_state"] == "INTERRUPTED"
    assert receipt["interruption_reason"] == "AUTHORIZED_CANCEL"


def test_stock_decision_records_unexpected_v2_failure(monkeypatch) -> None:
    recorded: list[str] = []

    async def fail(*args: object, **kwargs: object) -> dict[str, object]:
        raise RuntimeError("unexpected")

    monkeypatch.setattr(
        stock_decision,
        "get_settings",
        lambda: SimpleNamespace(visible_stock_decision_engine="v2_accepted"),
    )
    monkeypatch.setattr(stock_decision, "generate_v2", fail)
    monkeypatch.setattr(
        stock_decision,
        "record_unexpected_terminal_failure",
        lambda packet_id, claim_id, reason: recorded.append(reason),
    )
    args = SimpleNamespace(packet_id="packet", claim_id="claim", timeout=1800)

    with pytest.raises(RuntimeError, match="unexpected"):
        asyncio.run(stock_decision._run(args))

    assert recorded == ["UNEXPECTED:RuntimeError"]


def test_natural_proof_does_not_count_pilot_delivery_as_explicit_v2() -> None:
    counts = ExplicitV2NaturalProofCounts(
        ai_accepted_total=9,
        ai_market_sent=1,
        explicit_v2_stock_accepted=0,
        explicit_v2_stock_sent=0,
        pilot_ai_assisted_sent=8,
        deterministic_fallback_sent=0,
        duplicate_sent=0,
    )

    result = evaluate_explicit_v2_natural_proof(counts, expected_stock_count=8)

    assert result["status"] == "FAIL"
    assert result["checks"]["ai_market_sent"] is True
    assert result["checks"]["explicit_v2_stock_sent"] is False


def test_natural_proof_requires_exact_explicit_v2_scope() -> None:
    counts = ExplicitV2NaturalProofCounts(
        ai_accepted_total=9,
        ai_market_sent=1,
        explicit_v2_stock_accepted=8,
        explicit_v2_stock_sent=8,
        pilot_ai_assisted_sent=0,
        deterministic_fallback_sent=0,
        duplicate_sent=0,
    )

    assert evaluate_explicit_v2_natural_proof(
        counts,
        expected_stock_count=8,
    )["status"] == "PASS"


def test_daily_review_skill_respects_command_owned_timeout() -> None:
    skill = Path(".agents/skills/thesis-monitor-daily-review/SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "single authoritative model-generation timeout" in skill
    assert "Do not manually interrupt a healthy child" in skill
    assert "ACTIVE` or `MODEL_ACTIVE` with no candidate is not failure" in skill
