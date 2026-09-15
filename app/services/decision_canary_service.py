from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import Field

from app.config import Settings, get_settings
from app.services.cross_market_decision_engine_service import (
    DecisionCandidate,
    DecisionEvidencePacket,
    EvidenceCategory,
    EvidencePolarity,
    EvidenceReasonRole,
    FrozenModel,
    PolarityEvidenceClaim,
    canonicalize_candidate_metadata,
    compact_ai_context,
    decision_message_quality,
    render_shadow_decision,
    validate_decision_candidate,
)


CONTRACT_VERSION = "cross-market-decision-bounded-canary-v1"
OUTPUT_CONTRACT = "cross-market-decision-canary-output-v1"
ARTIFACT_CONTRACT = "cross-market-decision-canary-artifact-v1"
RECEIPT_CONTRACT = "cross-market-decision-canary-receipt-v1"
CANARY_STATE = "canary"
READY_STATE = "test_sink_ready"
CANARY_REASONING_MODEL = "gpt-5.6-sol"
CANARY_REASONING_EFFORT = "xhigh"
CONTINUITY_STATE_CONTRACT = "cross-market-decision-canary-continuity-state-v1"
POLARITY_CONTRACT = "decision-evidence-polarity-v1"
_HANGUL_SYLLABLE = re.compile(r"[가-힣]")


class DecisionCanaryContinuityBaseline(FrozenModel):
    ticker: str
    evidence_sha256: str
    candidate: DecisionCandidate
    source: str


class DecisionCanaryContext(FrozenModel):
    contract: Literal["cross-market-decision-bounded-canary-v1"] = CONTRACT_VERSION
    packet_id: str
    claim_id: str
    market: Literal["kr", "us"]
    assessment_date: str
    source_packet_sha256: str
    selected_subjects: tuple[str, ...] = Field(min_length=2, max_length=2)
    evidence_packets: tuple[DecisionEvidencePacket, ...] = Field(min_length=2, max_length=2)
    continuity_baselines: tuple[DecisionCanaryContinuityBaseline, ...] = Field(
        default=(), max_length=2
    )
    prepared_at: str


class DecisionCanaryBatchOutput(FrozenModel):
    contract: Literal["cross-market-decision-canary-output-v1"] = OUTPUT_CONTRACT
    packet_id: str
    claim_id: str
    market: Literal["kr", "us"]
    assessment_date: str
    decisions: tuple[DecisionCandidate, ...] = Field(min_length=2, max_length=2)


class DecisionCanaryBlock(FrozenModel):
    ticker: str
    decision: Literal["BUY", "HOLD", "SELL"]
    text: str = Field(min_length=1, max_length=2200)


class DecisionCanaryArtifact(FrozenModel):
    contract: Literal["cross-market-decision-canary-artifact-v1"] = ARTIFACT_CONTRACT
    status: Literal["PASS"] = "PASS"
    packet_id: str
    claim_id: str
    market: Literal["kr", "us"]
    assessment_date: str
    source_packet_sha256: str
    selected_subjects: tuple[str, ...] = Field(min_length=2, max_length=2)
    reasoning_model: Literal["gpt-5.6-sol"] = CANARY_REASONING_MODEL
    reasoning_effort: Literal["xhigh"] = CANARY_REASONING_EFFORT
    evidence_packets: tuple[DecisionEvidencePacket, ...] = Field(min_length=2, max_length=2)
    decisions: tuple[DecisionCandidate, ...] = Field(min_length=2, max_length=2)
    blocks: tuple[DecisionCanaryBlock, ...] = Field(min_length=2, max_length=2)
    message_quality: dict[str, object]
    validated_at: str


class DecisionCanaryStateEntry(FrozenModel):
    ticker: str
    market: Literal["kr", "us"]
    evidence_sha256: str
    candidate: DecisionCandidate
    source_packet_id: str
    assessment_date: str
    updated_at: str


class DecisionCanaryState(FrozenModel):
    contract: Literal["cross-market-decision-canary-continuity-state-v1"] = (
        CONTINUITY_STATE_CONTRACT
    )
    state: Literal["test_sink_ready", "canary"]
    entries: tuple[DecisionCanaryStateEntry, ...]


class DecisionPolarityPlan(FrozenModel):
    contract: Literal["decision-evidence-polarity-v1"] = POLARITY_CONTRACT
    ticker: str
    decision: Literal["BUY", "HOLD", "SELL"]
    evidence_sha256: str
    buy_case_evidence: tuple[PolarityEvidenceClaim, ...] = Field(min_length=1, max_length=3)
    sell_case_evidence: tuple[PolarityEvidenceClaim, ...] = Field(min_length=1, max_length=3)
    neutral_context_evidence: tuple[PolarityEvidenceClaim, ...] = Field(
        default=(), max_length=3
    )


class DecisionPolarityPlanBatch(FrozenModel):
    contract: Literal["decision-evidence-polarity-batch-v1"] = (
        "decision-evidence-polarity-batch-v1"
    )
    plans: tuple[DecisionPolarityPlan, ...] = Field(min_length=1, max_length=20)


def decision_polarity_errors(
    packet: DecisionEvidencePacket,
    candidate: DecisionCandidate,
    *,
    require_directional: bool = True,
) -> tuple[str, ...]:
    return polarity_claim_errors(
        packet,
        buy_case_evidence=candidate.buy_case_evidence,
        sell_case_evidence=candidate.sell_case_evidence,
        neutral_context_evidence=candidate.neutral_context_evidence,
        require_directional=require_directional,
    )


def polarity_claim_errors(
    packet: DecisionEvidencePacket,
    *,
    buy_case_evidence: tuple[PolarityEvidenceClaim, ...],
    sell_case_evidence: tuple[PolarityEvidenceClaim, ...],
    neutral_context_evidence: tuple[PolarityEvidenceClaim, ...],
    require_directional: bool = True,
) -> tuple[str, ...]:
    refs = {row.ref_id: row for row in packet.evidence}
    sections: tuple[
        tuple[str, tuple[PolarityEvidenceClaim, ...], EvidencePolarity], ...
    ] = (
        ("buy", buy_case_evidence, EvidencePolarity.BULLISH),
        ("sell", sell_case_evidence, EvidencePolarity.BEARISH),
        ("neutral", neutral_context_evidence, EvidencePolarity.NEUTRAL),
    )
    errors: list[str] = []
    if require_directional and not buy_case_evidence:
        errors.append("buy_case_evidence_missing")
    if require_directional and not sell_case_evidence:
        errors.append("sell_case_evidence_missing")
    if require_directional and len(buy_case_evidence) != 1:
        errors.append("buy_case_compact_selection_requires_one")
    if require_directional and len(sell_case_evidence) != 1:
        errors.append("sell_case_compact_selection_requires_one")
    selected: dict[str, set[str]] = {name: set() for name, _claims, _expected in sections}
    timing_categories = {
        EvidenceCategory.PRICE_STRUCTURE,
        EvidenceCategory.TECHNICAL_FEATURE,
        EvidenceCategory.FLOWS,
        EvidenceCategory.MARKET,
    }
    for name, claims, expected in sections:
        for claim in claims:
            if claim.polarity != expected:
                errors.append(f"{name}_case_wrong_polarity:{claim.polarity}")
            if (
                claim.reason_role == EvidenceReasonRole.DATA_QUALITY
                and claim.polarity != EvidencePolarity.NEUTRAL
            ):
                errors.append(f"data_quality_directional_polarity:{name}")
            for ref_id in claim.evidence_refs:
                ref = refs.get(ref_id)
                if ref is None:
                    errors.append(f"polarity_unknown_evidence_ref:{ref_id}")
                    continue
                if not ref.source_ref or not ref.as_of:
                    errors.append(f"polarity_lineage_incomplete:{ref_id}")
                selected[name].add(ref_id)
                if (
                    claim.reason_role == EvidenceReasonRole.TIMING_ONLY
                    and ref.category not in timing_categories
                ):
                    errors.append(f"timing_role_non_timing_ref:{ref_id}")
    overlap = selected["buy"] & selected["sell"]
    if overlap:
        errors.extend(f"evidence_selected_on_both_sides:{ref_id}" for ref_id in sorted(overlap))
    for name, claims, _expected in sections[:2]:
        flattened = [ref_id for claim in claims for ref_id in claim.evidence_refs]
        if len(flattened) != len(set(flattened)):
            errors.append(f"duplicate_{name}_case_evidence_ref")
        if claims and all(
            claim.reason_role == EvidenceReasonRole.TIMING_ONLY for claim in claims
        ):
            errors.append(f"{name}_case_owned_only_by_timing")
    return tuple(dict.fromkeys(errors))


def apply_decision_polarity_plan(
    packet: DecisionEvidencePacket,
    candidate: DecisionCandidate,
    plan: DecisionPolarityPlan,
) -> DecisionCandidate:
    if (
        plan.ticker != packet.ticker
        or candidate.ticker != packet.ticker
        or plan.decision != candidate.decision
        or plan.evidence_sha256 != packet.evidence_sha256
    ):
        raise ValueError("decision_polarity_plan_identity_mismatch")
    enriched = candidate.model_copy(
        update={
            "buy_case_evidence": plan.buy_case_evidence,
            "sell_case_evidence": plan.sell_case_evidence,
            "neutral_context_evidence": plan.neutral_context_evidence,
        }
    )
    enriched = canonicalize_candidate_metadata(packet, enriched)
    validation = validate_decision_candidate(packet, enriched)
    errors = decision_polarity_errors(packet, enriched)
    if not validation.valid or errors:
        raise ValueError(
            "decision_polarity_plan_invalid:"
            + ",".join((*validation.errors, *errors))
        )
    return enriched


def _csv_subjects(value: str) -> tuple[str, ...]:
    subjects = tuple(item.strip().upper() for item in value.split(",") if item.strip())
    if len(subjects) != len(set(subjects)):
        raise ValueError("duplicate_decision_canary_subject")
    return subjects


def configured_decision_canary_subjects(
    market: Literal["kr", "us"],
    *,
    settings: Settings | None = None,
) -> tuple[str, ...]:
    current = settings or get_settings()
    raw = (
        current.decision_engine_canary_kr_subjects
        if market == "kr"
        else current.decision_engine_canary_us_subjects
    )
    return _csv_subjects(raw)


def decision_canary_armed(*, settings: Settings | None = None) -> bool:
    current = settings or get_settings()
    return bool(
        current.decision_engine_canary_enabled and current.decision_engine_state == CANARY_STATE
    )


def decision_canary_preconditions(*, settings: Settings | None = None) -> dict[str, object]:
    current = settings or get_settings()
    kr = configured_decision_canary_subjects("kr", settings=current)
    us = configured_decision_canary_subjects("us", settings=current)
    checks = {
        "enabled": current.decision_engine_canary_enabled,
        "state_is_canary": current.decision_engine_state == CANARY_STATE,
        "kr_exactly_two": len(kr) == 2,
        "us_exactly_two": len(us) == 2,
        "cross_market_unique": len(set((*kr, *us))) == 4,
    }
    return {
        "contract": CONTRACT_VERSION,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "kr_subjects": list(kr),
        "us_subjects": list(us),
        "global_decision_block_enabled": 0,
        "automatic_subject_substitution": 0,
    }


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json_schema(value: object) -> object:
    if isinstance(value, dict):
        transformed: dict[str, object] = {}
        for key, item in value.items():
            if key in {"default", "discriminator"}:
                continue
            target = "anyOf" if key == "oneOf" else key
            if target in transformed:
                raise ValueError(f"strict_schema_keyword_collision:{target}")
            transformed[target] = strict_json_schema(item)
        properties = transformed.get("properties")
        if isinstance(properties, dict):
            transformed["required"] = list(properties)
            transformed["additionalProperties"] = False
        return transformed
    if isinstance(value, list):
        return [strict_json_schema(item) for item in value]
    return value


def decision_canary_paths(
    final_review_path: Path,
    *,
    claim_id: str,
) -> dict[str, Path]:
    stem = final_review_path.stem
    parent = final_review_path.parent
    claim_stem = f"{stem}--{claim_id}"
    return {
        "context": parent.parent / "claims" / f"{claim_stem}.decision-context.json",
        "prompt": parent.parent / "claims" / f"{claim_stem}.decision-prompt.txt",
        "schema": parent.parent / "claims" / f"{claim_stem}.decision-schema.json",
        "temp": parent / f"{claim_stem}.decision.json.tmp",
        "final": parent / f"{stem}.decision-canary.json",
        "receipt": parent.parent / "claims" / f"{claim_stem}.decision-receipt.json",
        "log": parent.parent / "claims" / f"{claim_stem}.decision-cli.log",
    }


def decision_canary_state_path(*, settings: Settings | None = None) -> Path:
    current = settings or get_settings()
    return Path(current.data_dir) / "ai_review" / "decision_canary" / "state.json"


def load_decision_canary_state(*, settings: Settings | None = None) -> DecisionCanaryState | None:
    path = decision_canary_state_path(settings=settings)
    if not path.exists():
        return None
    return DecisionCanaryState.model_validate_json(path.read_text(encoding="utf-8"))


def write_decision_canary_state(
    state: DecisionCanaryState,
    *,
    settings: Settings | None = None,
) -> Path:
    path = decision_canary_state_path(settings=settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            state.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def advance_decision_canary_state(
    artifact: DecisionCanaryArtifact,
    *,
    settings: Settings | None = None,
    updated_at: datetime | None = None,
) -> Path:
    current_settings = settings or get_settings()
    existing = load_decision_canary_state(settings=current_settings)
    entries = {row.ticker: row for row in (existing.entries if existing else ())}
    evidence = {row.ticker: row for row in artifact.evidence_packets}
    timestamp = (updated_at or datetime.now(UTC)).astimezone(UTC).isoformat()
    for candidate in artifact.decisions:
        packet = evidence[candidate.ticker]
        entries[candidate.ticker] = DecisionCanaryStateEntry(
            ticker=candidate.ticker,
            market=artifact.market,
            evidence_sha256=packet.evidence_sha256,
            candidate=candidate,
            source_packet_id=artifact.packet_id,
            assessment_date=artifact.assessment_date,
            updated_at=timestamp,
        )
    state = DecisionCanaryState(
        state=current_settings.decision_engine_state,
        entries=tuple(entries[ticker] for ticker in sorted(entries)),
    )
    return write_decision_canary_state(state, settings=current_settings)


def build_decision_canary_context(
    *,
    packet: Mapping[str, object],
    claim_id: str,
    evidence_packets: Sequence[DecisionEvidencePacket],
    prepared_at: datetime | None = None,
    continuity_candidates: Mapping[str, DecisionCandidate] | None = None,
    continuity_source: str = "decision_canary_state",
    settings: Settings | None = None,
) -> DecisionCanaryContext:
    market = str(packet.get("market") or "").lower()
    if market not in {"kr", "us"}:
        raise ValueError("unsupported_decision_canary_market")
    typed_market: Literal["kr", "us"] = "kr" if market == "kr" else "us"
    subjects = configured_decision_canary_subjects(typed_market, settings=settings)
    if len(subjects) != 2:
        raise ValueError("decision_canary_requires_exactly_two_market_subjects")
    by_ticker = {row.ticker: row for row in evidence_packets}
    if set(by_ticker) != set(subjects):
        raise ValueError("decision_canary_subject_evidence_mismatch")
    packet_id = str(packet.get("packet_id") or "")
    assessment_date = str(packet.get("assessment_date") or "")
    if not packet_id or not assessment_date:
        raise ValueError("decision_canary_packet_identity_missing")
    for subject in subjects:
        evidence = by_ticker[subject]
        if evidence.packet_id != packet_id or evidence.assessment_date != assessment_date:
            raise ValueError("decision_canary_evidence_freshness_mismatch")
    ordered = tuple(by_ticker[subject] for subject in subjects)
    continuity: list[DecisionCanaryContinuityBaseline] = []
    for subject in subjects:
        candidate = (continuity_candidates or {}).get(subject)
        if candidate is None:
            continue
        validation = validate_decision_candidate(by_ticker[subject], candidate)
        if not validation.valid:
            raise ValueError(
                "decision_canary_continuity_candidate_invalid:"
                + subject
                + ":"
                + ",".join(validation.errors)
            )
        continuity.append(
            DecisionCanaryContinuityBaseline(
                ticker=subject,
                evidence_sha256=by_ticker[subject].evidence_sha256,
                candidate=candidate,
                source=continuity_source,
            )
        )
    return DecisionCanaryContext(
        packet_id=packet_id,
        claim_id=claim_id,
        market=typed_market,
        assessment_date=assessment_date,
        source_packet_sha256=canonical_sha256(packet),
        selected_subjects=subjects,
        evidence_packets=ordered,
        continuity_baselines=tuple(continuity),
        prepared_at=(prepared_at or datetime.now(UTC)).astimezone(UTC).isoformat(),
    )


def decision_canary_prompt(context: DecisionCanaryContext) -> str:
    packets = [compact_ai_context(packet) for packet in context.evidence_packets]
    return (
        """You own a bounded analytical BUY/HOLD/SELL decision for each supplied stock.

This is current investment research, not an order, automated trade, or position-size instruction. Use only the canonical evidence packets below. Do not browse or use later facts. Reason from integrity, thesis, earnings quality, expectations, valuation, catalysts and risks, market/flows, then price structure. Technical evidence may own timing but cannot silently own the long-horizon decision.

Hard contracts:
- Return exactly one decision for each supplied ticker and preserve packet_id, claim_id, market, assessment_date, ticker, horizon, and reasoning_grade.
- reasoning_grade is VERY_HIGH. Confidence is independent and measures evidence quality/convergence.
- BUY requires current long-horizon upside/asymmetry to materially exceed downside with sufficient business, earnings, and valuation support.
- HOLD requires material optionality, insufficient BUY asymmetry, no established downside dominance, a canonical hold_reason, and explicit why_not_buy/why_not_sell.
- SELL means current downside or impaired risk/reward materially dominates conditional upside; it does not require formal thesis invalidation or mandatory liquidation.
- Timing is independent. Use INSUFFICIENT for missing or materially conflicted timing evidence, not NEUTRAL.
- Every claim must cite exact complete ref_id values from that ticker. Never alter or invent a ref_id.
- Include company-specific decisive, supporting, opposing, unknown, timing, upgrade, and downgrade claims. Keep each claim concise enough for a production summary.
- supporting_evidence/opposing_evidence are relative to the final decision. They do not own directional BUY/SELL labels.
- The structured contract supports 1-3 directional claims, but this compact bounded canary must select exactly one strongest buy_case_evidence claim with polarity=BULLISH and exactly one strongest sell_case_evidence claim with polarity=BEARISH. Each claim needs an explicit reason_role and exact complete canonical evidence_refs.
- neutral_context_evidence may contain polarity=NEUTRAL context. Security identity, source validity, statement basis, and missing-data limitations are neutral unless separate owned economic evidence makes a directional claim.
- A HOLD needs credible evidence on both directional sides. A SELL still needs its strongest credible upside/optionality on the BUY side. A BUY still needs its strongest material risk on the SELL side.
- Do not reuse one evidence ref on both directional sides. Timing-only evidence must remain reason_role=TIMING_ONLY and cannot be the sole owner of either long-horizon side.
- selected_evidence_plan must contain every cited category. selected_numeric_fact_refs must be empty for this bounded production canary; do not put exact numbers in prose.
- Do not calculate or state a target, stop, order size, FCF valuation ratio, ROIC, CCC, runway months, or future return.
- Do not issue buy/sell imperatives or order language. BUY/HOLD/SELL is an analytical classification only.
- Do not target a class distribution and do not manufacture a BUY. Current BUY=0 is acceptable.
- For market=us, write every user-facing structured claim text in natural Korean. English is allowed only inside a Korean sentence for tickers, framework names, and proper nouns. Do not rely on post-render translation.
- Decision continuity is evidence-bound, not date-bound. When DECISION_CONTINUITY supplies the same evidence_sha256 as the current packet, preserve its BUY/HOLD/SELL classification. Do not change that classification by stylistic re-interpretation. Confidence, timing, and wording remain independently evidence-owned. A future packet with a different evidence_sha256 may be classified anew.
- Output only strict JSON matching the supplied schema.

IDENTITY:
"""
        + json.dumps(
            {
                "contract": OUTPUT_CONTRACT,
                "packet_id": context.packet_id,
                "claim_id": context.claim_id,
                "market": context.market,
                "assessment_date": context.assessment_date,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n\nDECISION_CONTINUITY:\n"
        + json.dumps(
            [row.model_dump(mode="json") for row in context.continuity_baselines],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n\nDECISION_EVIDENCE_PACKETS:\n"
        + json.dumps(
            packets,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )


def _decision_labels() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    confidence = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}
    confidence_reason = {
        "EVIDENCE_CONVERGENT": "핵심 근거 수렴",
        "MATERIAL_EVIDENCE_CONFLICT": "핵심 근거 충돌",
        "DATA_QUALITY_LIMIT": "자료 품질 제약",
        "VALUATION_LIMIT": "가치평가 제약",
        "SECURITY_BASIS_LIMIT": "증권 기준 제약",
        "ECONOMIC_PROOF_LIMIT": "경제성 검증 제약",
        "OTHER_DOCUMENTED": "문서화된 기타 제약",
    }
    timing = {
        "FAVORABLE": "우호적",
        "NEUTRAL": "중립",
        "UNFAVORABLE": "불리",
        "INSUFFICIENT": "판단 근거 부족",
    }
    return confidence, confidence_reason, timing


def decision_korean_localization_errors(
    packet: DecisionEvidencePacket,
    candidate: DecisionCandidate,
) -> tuple[str, ...]:
    if packet.market != "us":
        return ()
    claims = [
        ("timing_basis", candidate.timing_basis),
        ("decisive_reason", candidate.decisive_reason),
        ("why_not_buy", candidate.why_not_buy),
        ("why_not_sell", candidate.why_not_sell),
        ("upgrade_condition", candidate.upgrade_condition),
        ("downgrade_condition", candidate.downgrade_condition),
    ]
    groups = (
        ("supporting_evidence", candidate.supporting_evidence),
        ("opposing_evidence", candidate.opposing_evidence),
        ("buy_case_evidence", candidate.buy_case_evidence),
        ("sell_case_evidence", candidate.sell_case_evidence),
        ("neutral_context_evidence", candidate.neutral_context_evidence),
        ("unknowns", candidate.unknowns),
    )
    for name, rows in groups:
        claims.extend((f"{name}:{index}", claim) for index, claim in enumerate(rows))
    return tuple(
        f"us_claim_not_korean:{name}"
        for name, claim in claims
        if not _HANGUL_SYLLABLE.search(claim.text)
    )


def render_decision_canary_block(
    packet: DecisionEvidencePacket,
    candidate: DecisionCandidate,
) -> DecisionCanaryBlock:
    validation = validate_decision_candidate(packet, candidate)
    if not validation.valid:
        raise ValueError("decision_canary_candidate_invalid:" + ",".join(validation.errors))
    if candidate.selected_numeric_fact_refs:
        raise ValueError("decision_canary_numeric_detail_not_allowed")
    polarity_errors = decision_polarity_errors(packet, candidate)
    if polarity_errors:
        raise ValueError("decision_canary_polarity_invalid:" + ",".join(polarity_errors))
    localization_errors = decision_korean_localization_errors(packet, candidate)
    if localization_errors:
        raise ValueError(
            "decision_canary_korean_localization_invalid:"
            + packet.ticker
            + ":"
            + ",".join(localization_errors)
        )
    confidence, confidence_reason, timing = _decision_labels()
    lines = [
        f"🧠 AI 종합 판단: {candidate.decision}",
        f"추론등급: 매우 높음 | 판단 확신도: {confidence[candidate.confidence]}",
        f"확신 근거: {confidence_reason[candidate.confidence_reason]}",
        f"판단 기준: {candidate.horizon} | 단기 타이밍: {timing[candidate.timing]}",
        f"타이밍 근거: {candidate.timing_basis.text}",
        "",
        f"🎯 판단: {candidate.decisive_reason.text}",
    ]
    if candidate.decision == "HOLD":
        lines.extend(
            [
                f"• BUY가 아닌 이유: {candidate.why_not_buy.text}",
                f"• SELL이 아닌 이유: {candidate.why_not_sell.text}",
            ]
        )
    lines.extend(
        [
            "✅ BUY 쪽 근거:",
            *(f"• {claim.text}" for claim in candidate.buy_case_evidence),
            "⚠️ SELL 쪽 근거:",
            *(f"• {claim.text}" for claim in candidate.sell_case_evidence),
            f"🔼 상향 조건: {candidate.upgrade_condition.text}",
            f"🔽 하향 조건: {candidate.downgrade_condition.text}",
        ]
    )
    return DecisionCanaryBlock(
        ticker=packet.ticker,
        decision=candidate.decision,
        text="\n".join(lines),
    )


def validate_decision_canary_output(
    context: DecisionCanaryContext,
    output: DecisionCanaryBatchOutput,
    *,
    validated_at: datetime | None = None,
) -> DecisionCanaryArtifact:
    identity = (
        output.packet_id,
        output.claim_id,
        output.market,
        output.assessment_date,
    )
    expected_identity = (
        context.packet_id,
        context.claim_id,
        context.market,
        context.assessment_date,
    )
    if identity != expected_identity:
        raise ValueError("decision_canary_output_identity_mismatch")
    packets = {packet.ticker: packet for packet in context.evidence_packets}
    candidates = {
        candidate.ticker: canonicalize_candidate_metadata(packets[candidate.ticker], candidate)
        for candidate in output.decisions
        if candidate.ticker in packets
    }
    if set(candidates) != set(context.selected_subjects):
        raise ValueError("decision_canary_output_subject_mismatch")
    ordered_candidates = tuple(candidates[ticker] for ticker in context.selected_subjects)
    continuity = {row.ticker: row for row in context.continuity_baselines}
    for candidate in ordered_candidates:
        baseline = continuity.get(candidate.ticker)
        packet = packets[candidate.ticker]
        if (
            baseline is not None
            and baseline.evidence_sha256 == packet.evidence_sha256
            and baseline.candidate.decision != candidate.decision
        ):
            raise ValueError(f"decision_canary_unexplained_churn:{candidate.ticker}")
    if any(candidate.selected_numeric_fact_refs for candidate in ordered_candidates):
        raise ValueError("decision_canary_numeric_detail_not_allowed")
    for candidate in ordered_candidates:
        polarity_errors = decision_polarity_errors(packets[candidate.ticker], candidate)
        if polarity_errors:
            raise ValueError(
                "decision_canary_polarity_invalid:"
                + candidate.ticker
                + ":"
                + ",".join(polarity_errors)
            )
        localization_errors = decision_korean_localization_errors(
            packets[candidate.ticker], candidate
        )
        if localization_errors:
            raise ValueError(
                "decision_canary_korean_localization_invalid:"
                + candidate.ticker
                + ":"
                + ",".join(localization_errors)
            )
    rendered = tuple(
        render_shadow_decision(packets[candidate.ticker], candidate)
        for candidate in ordered_candidates
    )
    message_quality = decision_message_quality(rendered)
    if message_quality.get("status") != "PASS":
        raise ValueError("decision_canary_message_quality_failed")
    blocks = tuple(
        render_decision_canary_block(packets[candidate.ticker], candidate)
        for candidate in ordered_candidates
    )
    return DecisionCanaryArtifact(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        source_packet_sha256=context.source_packet_sha256,
        selected_subjects=context.selected_subjects,
        evidence_packets=context.evidence_packets,
        decisions=ordered_candidates,
        blocks=blocks,
        message_quality=message_quality,
        validated_at=(validated_at or datetime.now(UTC)).astimezone(UTC).isoformat(),
    )


def load_decision_canary_artifact(
    path: Path,
    *,
    packet: Mapping[str, object],
    claim_id: str,
    settings: Settings | None = None,
) -> DecisionCanaryArtifact:
    artifact = DecisionCanaryArtifact.model_validate_json(path.read_text(encoding="utf-8"))
    market = str(packet.get("market") or "")
    if market not in {"kr", "us"}:
        raise ValueError("decision_canary_artifact_market_invalid")
    typed_market: Literal["kr", "us"] = "kr" if market == "kr" else "us"
    expected = configured_decision_canary_subjects(typed_market, settings=settings)
    if (
        artifact.packet_id != str(packet.get("packet_id") or "")
        or artifact.claim_id != claim_id
        or artifact.market != typed_market
        or artifact.assessment_date != str(packet.get("assessment_date") or "")
        or artifact.source_packet_sha256 != canonical_sha256(packet)
        or artifact.selected_subjects != expected
    ):
        raise ValueError("decision_canary_artifact_freshness_or_scope_mismatch")
    packets = {row.ticker: row for row in artifact.evidence_packets}
    decisions = {row.ticker: row for row in artifact.decisions}
    blocks = {row.ticker: row for row in artifact.blocks}
    if (
        set(packets) != set(expected)
        or set(decisions) != set(expected)
        or set(blocks) != set(expected)
    ):
        raise ValueError("decision_canary_artifact_subject_mismatch")
    for ticker in expected:
        validation = validate_decision_candidate(packets[ticker], decisions[ticker])
        expected_block = render_decision_canary_block(packets[ticker], decisions[ticker])
        if (
            not validation.valid
            or decision_polarity_errors(packets[ticker], decisions[ticker])
            or blocks[ticker] != expected_block
        ):
            raise ValueError("decision_canary_artifact_validation_failed")
    return artifact


def insert_decision_canary_block(message: str, block: str) -> str:
    lines = message.splitlines()
    company_index = next(
        (index for index, line in enumerate(lines) if line.strip().startswith("🏢")),
        None,
    )
    if company_index is None:
        return f"{block}\n\n{message}"
    before = "\n".join(lines[: company_index + 1]).rstrip()
    after = "\n".join(lines[company_index + 1 :]).lstrip()
    return f"{before}\n\n{block}\n\n{after}" if after else f"{before}\n\n{block}"
