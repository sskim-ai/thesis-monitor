from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.jobs import accepted_decision_v2_runtime as runtime
from app.jobs.accepted_decision_v2_runtime import (
    V2CLIPathPreconditionError,
    _invoke_signed_in_codex,
    _paths,
    _signed_in_codex_bin,
)
from app.services.accepted_decision_v2_runtime_service import (
    accepted_v2_production_batch_schema_repair_prompt,
    accepted_v2_production_prompt,
    accepted_v2_production_repair_prompt,
    build_accepted_v2_production_context,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.preconfirmation_decision_v2_service import (
    PreconfirmationDecisionCandidate,
)


def _packet() -> DecisionEvidencePacket:
    return DecisionEvidencePacket(
        packet_id="packet-v2-runtime",
        ticker="TEST",
        company_name="Test Company",
        market="us",
        assessment_date="2026-08-30",
        horizon="12-36 months",
        evidence=(
            DecisionEvidenceRef(
                ref_id="canonical:chart:daily",
                category=EvidenceCategory.PRICE_STRUCTURE,
                label="canonical chart",
                statement="canonical chart summary",
                as_of="2026-08-30",
                source_ref="fixture",
            ),
            DecisionEvidenceRef(
                ref_id="technical-feature:daily:rsi14",
                category=EvidenceCategory.PRICE_STRUCTURE,
                label="low-level feature",
                statement="redundant low-level feature",
                as_of="2026-08-30",
                source_ref="fixture",
            ),
        ),
        prohibited_claims=(),
        evidence_sha256="fixture",
    )


def test_production_prompt_keeps_canonical_chart_and_omits_low_level_features() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-runtime",
        evidence_packets=(packet,),
    )

    prompt = accepted_v2_production_prompt(context)

    assert "canonical:chart:daily" in prompt
    assert "technical-feature:daily:rsi14" not in prompt
    assert '"claim_id":"claim-v2-runtime"' in prompt
    assert "Do not state or infer ROIC" in prompt


def test_bounded_repair_prompt_names_errors_and_keeps_exact_identity() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-runtime",
        evidence_packets=(packet,),
    )
    candidate = PreconfirmationDecisionCandidate.model_construct(ticker=packet.ticker)

    prompt = accepted_v2_production_repair_prompt(
        context,
        ticker=packet.ticker,
        rejected_candidate=candidate,
        validation_errors=("unsupported_metric_or_inference",),
    )

    assert "BOUNDED_VALIDATOR_REPAIR" in prompt
    assert "unsupported_metric_or_inference" in prompt
    assert '"claim_id":"claim-v2-runtime"' in prompt


def test_bounded_repair_prompt_explains_temporal_and_hold_contracts() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-runtime",
        evidence_packets=(packet,),
    )
    candidate = PreconfirmationDecisionCandidate.model_construct(ticker=packet.ticker)

    prompt = accepted_v2_production_repair_prompt(
        context,
        ticker=packet.ticker,
        rejected_candidate=candidate,
        validation_errors=(
            "future_maturity_evidence:cash conversion",
            "postconfirmation_hold_without_confirmed_maturity",
        ),
    )

    assert "never later than assessment_date" in prompt
    assert "post_confirmation_hold=false" in prompt
    assert "postconfirmation_hold_explanation=null" in prompt


def test_bounded_batch_schema_repair_keeps_scope_and_strict_errors() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-runtime",
        evidence_packets=(packet,),
    )

    prompt = accepted_v2_production_batch_schema_repair_prompt(
        context,
        subjects=(packet.ticker,),
        rejected_output={"candidates": [{"ticker": packet.ticker}]},
        validation_errors=(
            "candidates.0.driver_maturity.2:value_error:maturity_reference_polarity_overlap",
        ),
    )

    assert "BOUNDED_BATCH_SCHEMA_REPAIR" in prompt
    assert "maturity_reference_polarity_overlap" in prompt
    assert '"subjects":["TEST"]' in prompt
    assert '"claim_id":"claim-v2-runtime"' in prompt


def test_signed_in_codex_bin_prefers_explicit_executable(
    monkeypatch, tmp_path: Path
) -> None:
    executable = tmp_path / "codex"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setenv("CODEX_CLI_BIN", str(executable))

    assert _signed_in_codex_bin() == str(executable)


@pytest.mark.parametrize(
    ("schema_relative", "cwd_relative", "io_relative"),
    (
        (False, False, False),
        (True, True, False),
        (True, False, False),
        (True, True, True),
    ),
)
def test_signed_in_codex_invocation_normalizes_path_permutations(
    monkeypatch,
    tmp_path: Path,
    schema_relative: bool,
    cwd_relative: bool,
    io_relative: bool,
) -> None:
    relative_dir = Path("data/ai_review/claims")
    absolute_dir = tmp_path / relative_dir
    absolute_dir.mkdir(parents=True)
    prompt_absolute = absolute_dir / "claim.prompt.txt"
    schema_absolute = absolute_dir / "claim.schema.json"
    output_absolute = absolute_dir / "claim.output.json"
    log_absolute = absolute_dir / "claim.log"
    prompt_absolute.write_text("prompt", encoding="utf-8")
    schema_absolute.write_text("{}", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs["cwd"]
        Path(command[command.index("-o") + 1]).write_text("{}", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runtime, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(runtime.subprocess, "run", fake_run)

    _invoke_signed_in_codex(
        codex_bin="/bin/echo",
        prompt=(relative_dir / prompt_absolute.name) if io_relative else prompt_absolute,
        output=(relative_dir / output_absolute.name) if io_relative else output_absolute,
        log=(relative_dir / log_absolute.name) if io_relative else log_absolute,
        schema=(relative_dir / schema_absolute.name) if schema_relative else schema_absolute,
        cwd=relative_dir if cwd_relative else absolute_dir,
        timeout=30,
    )

    command = captured["command"]
    assert isinstance(command, list)
    assert Path(command[command.index("--output-schema") + 1]) == schema_absolute
    assert Path(command[command.index("-o") + 1]) == output_absolute
    assert captured["cwd"] == absolute_dir
    assert output_absolute.read_text(encoding="utf-8") == "{}"


def test_signed_in_codex_missing_schema_fails_before_subprocess(
    monkeypatch,
    tmp_path: Path,
) -> None:
    relative_dir = Path("data/ai_review/claims")
    absolute_dir = tmp_path / relative_dir
    absolute_dir.mkdir(parents=True)
    (absolute_dir / "claim.prompt.txt").write_text("prompt", encoding="utf-8")
    called = False

    def fake_run(*args, **kwargs):
        nonlocal called
        called = True
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runtime, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(runtime.subprocess, "run", fake_run)

    with pytest.raises(
        V2CLIPathPreconditionError,
        match="schema_exists",
    ):
        _invoke_signed_in_codex(
            codex_bin="/bin/echo",
            prompt=relative_dir / "claim.prompt.txt",
            output=relative_dir / "claim.output.json",
            log=relative_dir / "claim.log",
            schema=relative_dir / "missing.schema.json",
            cwd=relative_dir,
            timeout=30,
        )

    assert called is False


def test_signed_in_codex_invocation_creates_canonical_write_directories(
    monkeypatch,
    tmp_path: Path,
) -> None:
    relative_claims = Path("data/ai_review/claims")
    relative_outbox = Path("data/ai_review/outbox")
    claims = tmp_path / relative_claims
    claims.mkdir(parents=True)
    (claims / "claim.prompt.txt").write_text("prompt", encoding="utf-8")
    (claims / "claim.schema.json").write_text("{}", encoding="utf-8")

    def fake_run(command, **kwargs):
        Path(command[command.index("-o") + 1]).write_text("{}", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runtime, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(runtime.subprocess, "run", fake_run)

    _invoke_signed_in_codex(
        codex_bin="/bin/echo",
        prompt=relative_claims / "claim.prompt.txt",
        output=relative_outbox / "claim.output.json",
        log=relative_outbox / "logs" / "claim.log",
        schema=relative_claims / "claim.schema.json",
        cwd=relative_claims,
        timeout=30,
    )

    assert (tmp_path / relative_outbox / "claim.output.json").is_file()
    assert (tmp_path / relative_outbox / "logs" / "claim.log").is_file()


def test_run50_natural_claim_paths_use_one_canonical_repository_root(
    monkeypatch,
    tmp_path: Path,
) -> None:
    claim_id = "44ef5bbe-2ae7-427e-bf00-ec2c8e8983a1"
    packet_id = "2026-09-01-kr-run-50-a601ddc0620a"
    final_relative = Path(
        "data/ai_review/outbox/"
        f"{packet_id}--daily-review-v3.10--dc747fff8565.json"
    )
    monkeypatch.setattr(runtime, "_repository_root", lambda: tmp_path)

    paths = _paths({"final_output_path": str(final_relative)}, claim_id)
    expected_claims_dir = tmp_path / "data/ai_review/claims"
    expected_schema = expected_claims_dir / (
        f"{final_relative.stem}--{claim_id}.decision-v2-schema.json"
    )

    assert paths["schema"] == expected_schema
    assert paths["schema"].is_absolute()
    assert str(paths["schema"]).count("data/ai_review/claims") == 1

    expected_claims_dir.mkdir(parents=True)
    paths["prompt"].write_text("prompt", encoding="utf-8")
    paths["schema"].write_text("{}", encoding="utf-8")
    paths["temp"].parent.mkdir(parents=True)
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs["cwd"]
        Path(command[command.index("-o") + 1]).write_text("{}", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runtime.subprocess, "run", fake_run)
    _invoke_signed_in_codex(
        codex_bin="/bin/echo",
        prompt=paths["prompt"],
        output=paths["temp"],
        log=paths["log"],
        schema=paths["schema"],
        cwd=Path("data/ai_review/claims"),
        timeout=30,
    )

    command = captured["command"]
    assert isinstance(command, list)
    assert Path(command[command.index("--output-schema") + 1]) == expected_schema
    assert captured["cwd"] == expected_claims_dir
