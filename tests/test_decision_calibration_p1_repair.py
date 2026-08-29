from __future__ import annotations

from app.services.cross_market_decision_engine_service import (
    DecisionCandidate,
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
    EvidenceClaim,
    canonicalize_candidate_metadata,
)
from scripts.cross_market_ai_decision_engine_v1 import _received_quality
from scripts.decision_calibration_p1_repair import (
    CONFIDENCE_CASES,
    TIMING_CASES,
    _controls,
    _review_cases,
)


def _claim(text: str = "근거") -> EvidenceClaim:
    return EvidenceClaim(text=text, evidence_refs=("ref:one",))


def _candidate(
    ticker: str,
    *,
    decision: str = "HOLD",
    hold_reason: str = "BALANCED_EVIDENCE",
    confidence: str = "MEDIUM",
    timing: str = "NEUTRAL",
) -> DecisionCandidate:
    return DecisionCandidate(
        ticker=ticker,
        decision=decision,
        reasoning_grade="VERY_HIGH",
        confidence=confidence,
        confidence_reason="ECONOMIC_PROOF_LIMIT",
        horizon="12-36개월",
        timing=timing,
        timing_basis=_claim("타이밍 근거"),
        hold_reason=hold_reason,
        decisive_reason=_claim("결정 근거"),
        why_not_buy=_claim("BUY 제외 근거"),
        why_not_sell=_claim("SELL 제외 근거"),
        supporting_evidence=(_claim("지지 근거"),),
        opposing_evidence=(_claim("반대 근거"),),
        unknowns=(_claim("미확인 근거"),),
        upgrade_condition=_claim("상향 조건"),
        downgrade_condition=_claim("하향 조건"),
        selected_evidence_plan=(
            EvidenceCategory.THESIS,
            EvidenceCategory.RISKS,
            EvidenceCategory.TECHNICAL_FEATURE,
        ),
    )


def test_review_cases_include_instruction_targets_and_decision_flips() -> None:
    tickers = sorted(set((*TIMING_CASES, *CONFIDENCE_CASES, "HUT", "RXRX")))
    prior = {ticker: {"ticker": ticker, "final_decision": "HOLD"} for ticker in tickers}
    blind = {ticker: {"candidate": {"decision": "HOLD"}} for ticker in tickers}
    blind["RXRX"] = {"candidate": {"decision": "SELL"}}

    cases = _review_cases(prior, blind)

    assert set(TIMING_CASES).issubset(cases)
    assert set(CONFIDENCE_CASES).issubset(cases)
    assert cases["HUT"] == ("HUT_TAXONOMY",)
    assert cases["RXRX"] == ("DECISION",)


def test_controls_require_semantic_boundary_and_sell_controls() -> None:
    candidates = {
        "HUT": _candidate(
            "HUT",
            hold_reason="OPTIONALITY_OFFSETS_DOWNSIDE",
            confidence="LOW",
            timing="UNFAVORABLE",
        ),
        "CRCL": _candidate("CRCL", confidence="LOW", timing="INSUFFICIENT"),
        **{
            ticker: _candidate(
                ticker,
                decision="SELL",
                hold_reason="NOT_HOLD",
                timing="UNFAVORABLE",
            )
            for ticker in ("RXRX", "TSLA", "WULF")
        },
    }
    for ticker in set((*TIMING_CASES, *CONFIDENCE_CASES)) - set(candidates):
        candidates[ticker] = _candidate(ticker)

    controls = _controls(candidates)

    assert all(controls.values())


def test_received_quality_requires_calibrated_fields_and_hold_boundary() -> None:
    complete = "\n".join(
        (
            "AI 종합 판단: HOLD",
            "추론등급: 매우 높음 | 판단 확신도: 낮음",
            "판단 기준: 경제성 검증 제약",
            "단기 타이밍: 불리",
            "결정적 이유",
            "왜 BUY가 아닌가:",
            "왜 SELL이 아닌가:",
            "반대 근거",
            "상향 조건:",
            "하향 조건:",
        )
    )
    assert _received_quality(complete)["status"] == "PASS"
    assert _received_quality(complete.replace("하향 조건:", ""))["status"] == "FAIL"
    assert _received_quality(complete.replace("왜 SELL이 아닌가:", ""))["status"] == "FAIL"


def test_canonicalized_plan_round_trips_all_evidence_categories() -> None:
    candidate = _candidate("TEST")
    claims = [
        EvidenceClaim(text=f"근거 {index}", evidence_refs=(f"ref:{index}",)) for index in range(14)
    ]
    candidate = candidate.model_copy(
        update={
            "decisive_reason": claims[0],
            "timing_basis": claims[1],
            "why_not_buy": claims[2],
            "why_not_sell": claims[3],
            "supporting_evidence": tuple(claims[4:8]),
            "opposing_evidence": tuple(claims[8:12]),
            "unknowns": (claims[12],),
            "upgrade_condition": claims[13],
            "downgrade_condition": claims[0],
        }
    )
    packet = DecisionEvidencePacket(
        packet_id="packet",
        ticker="TEST",
        company_name="Test",
        market="us",
        assessment_date="2026-08-29",
        horizon="12-36개월",
        evidence=tuple(
            DecisionEvidenceRef(
                ref_id=f"ref:{index}",
                category=category,
                label=str(category),
                statement="근거",
                source_ref="fixture",
            )
            for index, category in enumerate(EvidenceCategory)
        ),
        prohibited_claims=(),
        evidence_sha256="fixture",
    )

    canonical = canonicalize_candidate_metadata(packet, candidate)

    assert len(canonical.selected_evidence_plan) == len(EvidenceCategory) == 14
    assert DecisionCandidate.model_validate(canonical.model_dump()) == canonical
