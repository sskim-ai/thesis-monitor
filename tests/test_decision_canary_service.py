from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.services.cross_market_decision_engine_service import (
    DecisionCandidate,
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
    EvidenceClaim,
    EvidencePolarity,
    EvidenceReasonRole,
    PolarityEvidenceClaim,
)
from app.services.decision_canary_service import (
    DecisionCanaryBatchOutput,
    advance_decision_canary_state,
    build_decision_canary_context,
    configured_decision_canary_subjects,
    decision_canary_armed,
    decision_canary_prompt,
    decision_korean_localization_errors,
    decision_polarity_errors,
    decision_canary_preconditions,
    insert_decision_canary_block,
    load_decision_canary_state,
    validate_decision_canary_output,
)


def _settings(
    *, enabled: bool = True, state: str = "canary", data_dir: str = "."
) -> SimpleNamespace:
    return SimpleNamespace(
        decision_engine_canary_enabled=enabled,
        decision_engine_state=state,
        decision_engine_canary_kr_subjects="003690,000660",
        decision_engine_canary_us_subjects="GOOGL,RXRX",
        data_dir=data_dir,
    )


def _evidence(ticker: str) -> DecisionEvidencePacket:
    rows = (
        ("thesis", EvidenceCategory.THESIS),
        ("earnings", EvidenceCategory.EARNINGS),
        ("expectations", EvidenceCategory.EXPECTATIONS),
        ("risks", EvidenceCategory.RISKS),
        ("price", EvidenceCategory.PRICE_STRUCTURE),
        ("unknown", EvidenceCategory.UNKNOWN),
    )
    return DecisionEvidencePacket(
        packet_id="2026-08-29-us-run-canary",
        ticker=ticker,
        company_name=f"{ticker} Inc",
        market="us",
        assessment_date="2026-08-29",
        horizon="12-24개월",
        evidence=tuple(
            DecisionEvidenceRef(
                ref_id=f"{ticker}:{name}",
                category=category,
                label=name,
                statement=f"{ticker} {name} 근거",
                as_of="2026-08-29",
                source_ref=f"stock.{name}",
            )
            for name, category in rows
        ),
        prohibited_claims=("order",),
        evidence_sha256=f"sha-{ticker}",
    )


def _claim(ticker: str, phrase: str) -> EvidenceClaim:
    return EvidenceClaim(text=phrase, evidence_refs=(f"{ticker}:thesis",))


def _candidate(ticker: str, phrase: str) -> DecisionCandidate:
    return DecisionCandidate(
        ticker=ticker,
        decision="HOLD",
        reasoning_grade="VERY_HIGH",
        confidence="MEDIUM",
        confidence_reason="MATERIAL_EVIDENCE_CONFLICT",
        horizon="12-24개월",
        timing="NEUTRAL",
        timing_basis=EvidenceClaim(
            text=f"{phrase} 단기 구조는 방향 확정을 유보하게 합니다.",
            evidence_refs=(f"{ticker}:price",),
        ),
        hold_reason="BALANCED_EVIDENCE",
        decisive_reason=_claim(ticker, f"{phrase} 선택지와 위험이 함께 남아 있습니다."),
        why_not_buy=EvidenceClaim(
            text=f"{phrase} 기대 검증이 더 필요합니다.",
            evidence_refs=(f"{ticker}:expectations",),
        ),
        why_not_sell=EvidenceClaim(
            text=f"{phrase} 장기 선택지가 아직 유효합니다.",
            evidence_refs=(f"{ticker}:thesis",),
        ),
        supporting_evidence=(
            EvidenceClaim(
                text=f"{phrase} 실적 근거는 논리 유지와 양립합니다.",
                evidence_refs=(f"{ticker}:earnings",),
            ),
        ),
        opposing_evidence=(
            EvidenceClaim(
                text=f"{phrase} 기대 부담은 추가 확신을 제한합니다.",
                evidence_refs=(f"{ticker}:risks",),
            ),
        ),
        buy_case_evidence=(
            PolarityEvidenceClaim(
                text=f"{phrase} 실적 근거는 장기 선택지를 지지합니다.",
                evidence_refs=(f"{ticker}:earnings",),
                polarity=EvidencePolarity.BULLISH,
                reason_role=EvidenceReasonRole.FUNDAMENTAL,
            ),
        ),
        sell_case_evidence=(
            PolarityEvidenceClaim(
                text=f"{phrase} 기대 부담은 하방 위험을 높입니다.",
                evidence_refs=(f"{ticker}:risks",),
                polarity=EvidencePolarity.BEARISH,
                reason_role=EvidenceReasonRole.FUNDAMENTAL,
            ),
        ),
        unknowns=(
            EvidenceClaim(
                text=f"{phrase} 다음 실적의 지속성은 아직 미확인입니다.",
                evidence_refs=(f"{ticker}:unknown",),
            ),
        ),
        upgrade_condition=_claim(ticker, f"{phrase} 실적 증명이 이어지면 상향합니다."),
        downgrade_condition=EvidenceClaim(
            text=f"{phrase} 핵심 실행이 훼손되면 하향합니다.",
            evidence_refs=(f"{ticker}:risks",),
        ),
        selected_numeric_fact_refs=(),
        selected_evidence_plan=(
            EvidenceCategory.THESIS,
            EvidenceCategory.EARNINGS,
            EvidenceCategory.EXPECTATIONS,
            EvidenceCategory.RISKS,
            EvidenceCategory.PRICE_STRUCTURE,
            EvidenceCategory.UNKNOWN,
        ),
    )


def test_canary_control_plane_requires_exact_subject_scope() -> None:
    settings = _settings()
    assert decision_canary_armed(settings=settings) is True
    assert configured_decision_canary_subjects("us", settings=settings) == (
        "GOOGL",
        "RXRX",
    )
    assert decision_canary_preconditions(settings=settings)["status"] == "PASS"
    assert decision_canary_armed(settings=_settings(enabled=False)) is False


def test_context_output_and_continuity_are_evidence_bound(tmp_path) -> None:
    packet = {
        "packet_id": "2026-08-29-us-run-canary",
        "market": "us",
        "assessment_date": "2026-08-29",
    }
    context = build_decision_canary_context(
        packet=packet,
        claim_id="claim-1",
        evidence_packets=(_evidence("GOOGL"), _evidence("RXRX")),
        continuity_candidates={
            "GOOGL": _candidate("GOOGL", "광고와 클라우드의 수익화"),
            "RXRX": _candidate("RXRX", "임상 실행과 자금 소요"),
        },
        prepared_at=datetime(2026, 8, 29, tzinfo=UTC),
        settings=_settings(),
    )
    output = DecisionCanaryBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        decisions=(
            _candidate("GOOGL", "광고와 클라우드의 수익화"),
            _candidate("RXRX", "임상 실행과 자금 소요"),
        ),
    )
    artifact = validate_decision_canary_output(
        context,
        output,
        validated_at=datetime(2026, 8, 29, tzinfo=UTC),
    )

    assert artifact.status == "PASS"
    assert artifact.reasoning_effort == "xhigh"
    assert artifact.selected_subjects == ("GOOGL", "RXRX")
    assert all(not row.selected_numeric_fact_refs for row in artifact.decisions)
    assert artifact.message_quality["status"] == "PASS"
    assert "natural Korean" in decision_canary_prompt(context)
    assert all("주문·자동매매" in block.text for block in artifact.blocks)
    assert all("실적 근거는 장기 선택지를 지지합니다" in block.text for block in artifact.blocks)
    assert all("기대 부담은 하방 위험을 높입니다" in block.text for block in artifact.blocks)

    stale = output.model_copy(update={"claim_id": "claim-2"})
    with pytest.raises(ValueError, match="identity_mismatch"):
        validate_decision_canary_output(context, stale)

    changed = output.model_copy(
        update={
            "decisions": (
                output.decisions[0].model_copy(
                    update={"decision": "SELL", "hold_reason": "NOT_HOLD"}
                ),
                output.decisions[1],
            )
        }
    )
    with pytest.raises(ValueError, match="unexplained_churn:GOOGL"):
        validate_decision_canary_output(context, changed)

    state_settings = _settings(data_dir=str(tmp_path))
    advance_decision_canary_state(
        artifact,
        settings=state_settings,
        updated_at=datetime(2026, 8, 29, tzinfo=UTC),
    )
    state = load_decision_canary_state(settings=state_settings)
    assert state is not None
    assert {row.ticker: row.candidate.decision for row in state.entries} == {
        "GOOGL": "HOLD",
        "RXRX": "HOLD",
    }


def test_us_canary_rejects_english_structured_claim_before_rendering() -> None:
    packet = {
        "packet_id": "2026-08-29-us-run-canary",
        "market": "us",
        "assessment_date": "2026-08-29",
    }
    context = build_decision_canary_context(
        packet=packet,
        claim_id="claim-1",
        evidence_packets=(_evidence("GOOGL"), _evidence("RXRX")),
        settings=_settings(),
    )
    googl = _candidate("GOOGL", "광고와 클라우드의 수익화")
    english = googl.model_copy(
        update={
            "decisive_reason": EvidenceClaim(
                text="Cloud optionality remains, but valuation support is incomplete.",
                evidence_refs=("GOOGL:thesis",),
            )
        }
    )
    output = DecisionCanaryBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        decisions=(english, _candidate("RXRX", "임상 실행과 자금 소요")),
    )

    assert decision_korean_localization_errors(_evidence("GOOGL"), english) == (
        "us_claim_not_korean:decisive_reason",
    )
    with pytest.raises(ValueError, match="korean_localization_invalid:GOOGL"):
        validate_decision_canary_output(context, output)


def test_canary_rejects_numeric_prose_and_inserts_without_replacing_base() -> None:
    packet = {
        "packet_id": "2026-08-29-us-run-canary",
        "market": "us",
        "assessment_date": "2026-08-29",
    }
    context = build_decision_canary_context(
        packet=packet,
        claim_id="claim-1",
        evidence_packets=(_evidence("GOOGL"), _evidence("RXRX")),
        settings=_settings(),
    )
    numeric = _candidate("GOOGL", "광고와 클라우드의 수익화").model_copy(
        update={"selected_numeric_fact_refs": ("GOOGL:price",)}
    )
    output = DecisionCanaryBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        decisions=(numeric, _candidate("RXRX", "임상 실행과 자금 소요")),
    )
    with pytest.raises(ValueError, match="numeric_detail_not_allowed"):
        validate_decision_canary_output(context, output)

    base = "🤖 기존 분석\n\n🏢 Alphabet(GOOGL)\n\n🎯 기존 핵심 판단"
    combined = insert_decision_canary_block(base, "🧠 AI 종합 판단: HOLD")
    assert "🤖 기존 분석" in combined
    assert "🎯 기존 핵심 판단" in combined
    assert combined.index("🏢 Alphabet") < combined.index("🧠 AI 종합 판단")
    assert combined.index("🧠 AI 종합 판단") < combined.index("🎯 기존 핵심 판단")


def test_polarity_contract_rejects_inversion_neutral_leakage_and_overlap() -> None:
    packet = _evidence("GOOGL")
    candidate = _candidate("GOOGL", "광고와 클라우드의 수익화")

    inverted = candidate.model_copy(
        update={
            "sell_case_evidence": (
                candidate.buy_case_evidence[0].model_copy(
                    update={"polarity": EvidencePolarity.BULLISH}
                ),
            )
        }
    )
    assert "sell_case_wrong_polarity:BULLISH" in decision_polarity_errors(
        packet, inverted
    )

    neutral_as_sell = candidate.model_copy(
        update={
            "sell_case_evidence": (
                PolarityEvidenceClaim(
                    text="재무제표와 증권 식별 기준을 확인했습니다.",
                    evidence_refs=("GOOGL:unknown",),
                    polarity=EvidencePolarity.BEARISH,
                    reason_role=EvidenceReasonRole.DATA_QUALITY,
                ),
            )
        }
    )
    assert "data_quality_directional_polarity:sell" in decision_polarity_errors(
        packet, neutral_as_sell
    )

    overlapping = candidate.model_copy(
        update={
            "sell_case_evidence": (
                PolarityEvidenceClaim(
                    text="같은 근거를 반대 방향에 중복 배치했습니다.",
                    evidence_refs=("GOOGL:earnings",),
                    polarity=EvidencePolarity.BEARISH,
                    reason_role=EvidenceReasonRole.FUNDAMENTAL,
                ),
            )
        }
    )
    assert "evidence_selected_on_both_sides:GOOGL:earnings" in decision_polarity_errors(
        packet, overlapping
    )


def test_polarity_contract_rejects_missing_and_timing_only_ownership() -> None:
    packet = _evidence("RXRX")
    candidate = _candidate("RXRX", "임상 실행과 자금 소요")
    missing = candidate.model_copy(update={"buy_case_evidence": ()})
    assert "buy_case_evidence_missing" in decision_polarity_errors(packet, missing)

    timing_only = candidate.model_copy(
        update={
            "buy_case_evidence": (
                PolarityEvidenceClaim(
                    text="가격 구조는 단기 선택지를 지지합니다.",
                    evidence_refs=("RXRX:price",),
                    polarity=EvidencePolarity.BULLISH,
                    reason_role=EvidenceReasonRole.TIMING_ONLY,
                ),
            )
        }
    )
    assert "buy_case_owned_only_by_timing" in decision_polarity_errors(
        packet, timing_only
    )
