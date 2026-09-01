from __future__ import annotations

from pathlib import Path

from app.jobs.accepted_decision_v2_runtime import _signed_in_codex_bin
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
