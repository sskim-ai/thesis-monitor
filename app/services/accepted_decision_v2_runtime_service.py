from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import Field

from app.config import Settings, get_settings
from app.services.accepted_decision_v2_service import (
    AcceptedDecisionPlan,
    AcceptedDecisionStatus,
    AcceptedV2Adjudication,
    RenderedProductionAcceptedDecision,
    render_accepted_v2_production,
    resolve_accepted_v2_decision,
    validate_accepted_v2_decision,
)
from app.services.cross_market_decision_engine_service import (
    Decision,
    DecisionEvidencePacket,
    FrozenModel,
    compact_ai_context,
)
from app.services.decision_canary_service import canonical_sha256
from app.services.preconfirmation_decision_v2_service import (
    PreconfirmationDecisionCandidate,
    validate_preconfirmation_candidate,
)


CONTRACT_VERSION = "v2-accepted-production-runtime-v1"
OUTPUT_CONTRACT = "v2-accepted-production-output-v1"
ARTIFACT_CONTRACT = "v2-accepted-production-artifact-v1"
STATE_CONTRACT = "v2-accepted-production-state-v1"
RECEIPT_CONTRACT = "v2-accepted-production-receipt-v1"
REASONING_MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "xhigh"


class AcceptedV2ProductionBaseline(FrozenModel):
    ticker: str
    market: Literal["kr", "us"]
    accepted_decision: Decision
    evidence_sha256: str
    accepted_decision_id: str
    source: str


class AcceptedV2ProductionContext(FrozenModel):
    contract: Literal["v2-accepted-production-runtime-v1"] = CONTRACT_VERSION
    packet_id: str
    claim_id: str
    market: Literal["kr", "us"]
    assessment_date: str
    source_packet_sha256: str
    selected_subjects: tuple[str, ...] = Field(min_length=1, max_length=20)
    evidence_packets: tuple[DecisionEvidencePacket, ...] = Field(min_length=1, max_length=20)
    prior_accepted: tuple[AcceptedV2ProductionBaseline, ...] = Field(
        default=(), max_length=20
    )
    prepared_at: str


class AcceptedV2ProductionBatchOutput(FrozenModel):
    contract: Literal["v2-accepted-production-output-v1"] = OUTPUT_CONTRACT
    packet_id: str
    claim_id: str
    market: Literal["kr", "us"]
    assessment_date: str
    candidates: tuple[PreconfirmationDecisionCandidate, ...] = Field(
        min_length=1, max_length=20
    )
    adjudications: tuple[AcceptedV2Adjudication, ...] = Field(default=(), max_length=20)


class AcceptedV2ProductionBlock(FrozenModel):
    ticker: str
    decision: Decision
    accepted_decision_id: str
    text: str = Field(min_length=1, max_length=2200)


class AcceptedV2ProductionArtifact(FrozenModel):
    contract: Literal["v2-accepted-production-artifact-v1"] = ARTIFACT_CONTRACT
    status: Literal["PASS", "PARTIAL_SAFE"]
    packet_id: str
    claim_id: str
    market: Literal["kr", "us"]
    assessment_date: str
    source_packet_sha256: str
    selected_subjects: tuple[str, ...] = Field(min_length=1, max_length=20)
    reasoning_model: Literal["gpt-5.6-sol"] = REASONING_MODEL
    reasoning_effort: Literal["xhigh"] = REASONING_EFFORT
    evidence_packets: tuple[DecisionEvidencePacket, ...] = Field(min_length=1, max_length=20)
    candidates: tuple[PreconfirmationDecisionCandidate, ...] = Field(
        min_length=1, max_length=20
    )
    accepted_plans: tuple[AcceptedDecisionPlan, ...] = Field(min_length=1, max_length=20)
    blocks: tuple[AcceptedV2ProductionBlock, ...] = Field(default=(), max_length=20)
    ready_count: int
    not_ready_count: int
    message_quality: dict[str, object]
    validated_at: str


class AcceptedV2ProductionStateEntry(FrozenModel):
    ticker: str
    market: Literal["kr", "us"]
    evidence_sha256: str
    accepted_plan: AcceptedDecisionPlan
    source_packet_id: str
    assessment_date: str
    updated_at: str


class AcceptedV2ProductionState(FrozenModel):
    contract: Literal["v2-accepted-production-state-v1"] = STATE_CONTRACT
    entries: tuple[AcceptedV2ProductionStateEntry, ...]


def v2_accepted_production_armed(*, settings: Settings | None = None) -> bool:
    current = settings or get_settings()
    return bool(
        current.visible_stock_decision_engine == "v2_accepted"
        and current.v2_production_enabled
        and current.v2_full_monitored_stock_coverage_target
        and current.v1_decision_rollback_available
    )


def accepted_v2_production_paths(
    final_review_path: Path,
    *,
    claim_id: str,
) -> dict[str, Path]:
    stem = final_review_path.stem
    parent = final_review_path.parent
    claim_stem = f"{stem}--{claim_id}"
    return {
        "context": parent.parent / "claims" / f"{claim_stem}.decision-v2-context.json",
        "schema": parent.parent / "claims" / f"{claim_stem}.decision-v2-schema.json",
        "prompt": parent.parent / "claims" / f"{claim_stem}.decision-v2-prompt.txt",
        "temp": parent / f"{claim_stem}.decision-v2.json.tmp",
        "final": parent / f"{stem}.decision-v2-accepted.json",
        "receipt": parent.parent / "claims" / f"{claim_stem}.decision-v2-receipt.json",
        "log": parent.parent / "claims" / f"{claim_stem}.decision-v2-cli.log",
    }


def accepted_v2_state_path(*, settings: Settings | None = None) -> Path:
    current = settings or get_settings()
    return Path(current.data_dir) / "ai_review" / "decision_v2" / "state.json"


def load_accepted_v2_state(
    *, settings: Settings | None = None
) -> AcceptedV2ProductionState | None:
    path = accepted_v2_state_path(settings=settings)
    if not path.exists():
        return None
    return AcceptedV2ProductionState.model_validate_json(path.read_text(encoding="utf-8"))


def write_accepted_v2_state(
    state: AcceptedV2ProductionState,
    *,
    settings: Settings | None = None,
) -> Path:
    path = accepted_v2_state_path(settings=settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def migration_baseline_path() -> Path:
    return Path(__file__).resolve().parents[1] / "resources" / "v2_accepted_migration_baseline.json"


def load_migration_baselines() -> dict[str, AcceptedV2ProductionBaseline]:
    value = json.loads(migration_baseline_path().read_text(encoding="utf-8"))
    rows = value.get("entries") if isinstance(value, Mapping) else None
    if not isinstance(rows, list):
        raise ValueError("v2_migration_baseline_invalid")
    entries = [AcceptedV2ProductionBaseline.model_validate(row) for row in rows]
    if len(entries) != len({row.ticker for row in entries}):
        raise ValueError("v2_migration_baseline_duplicate_ticker")
    return {row.ticker: row for row in entries}


def effective_prior_accepted(
    *,
    settings: Settings | None = None,
) -> dict[str, AcceptedV2ProductionBaseline]:
    baselines = load_migration_baselines()
    state = load_accepted_v2_state(settings=settings)
    for row in state.entries if state is not None else ():
        plan = row.accepted_plan
        if (
            plan.status == AcceptedDecisionStatus.READY
            and plan.accepted_decision is not None
            and plan.accepted_decision_id is not None
        ):
            baselines[row.ticker] = AcceptedV2ProductionBaseline(
                ticker=row.ticker,
                market=row.market,
                accepted_decision=plan.accepted_decision,
                evidence_sha256=row.evidence_sha256,
                accepted_decision_id=plan.accepted_decision_id,
                source="runtime_accepted_state",
            )
    return baselines


def build_accepted_v2_production_context(
    *,
    packet: Mapping[str, object],
    claim_id: str,
    evidence_packets: Sequence[DecisionEvidencePacket],
    prepared_at: datetime | None = None,
    settings: Settings | None = None,
) -> AcceptedV2ProductionContext:
    market = str(packet.get("market") or "").lower()
    if market not in {"kr", "us"}:
        raise ValueError("v2_production_market_invalid")
    typed_market: Literal["kr", "us"] = "kr" if market == "kr" else "us"
    stocks = [row for row in packet.get("stocks") or () if isinstance(row, Mapping)]
    subjects = tuple(str(row.get("ticker") or "").upper() for row in stocks)
    if not subjects or len(subjects) != len(set(subjects)):
        raise ValueError("v2_production_subject_inventory_invalid")
    by_ticker = {row.ticker: row for row in evidence_packets}
    if set(subjects) != set(by_ticker):
        raise ValueError("v2_production_evidence_scope_mismatch")
    packet_id = str(packet.get("packet_id") or "")
    assessment_date = str(packet.get("assessment_date") or "")
    for ticker in subjects:
        evidence = by_ticker[ticker]
        if (
            evidence.packet_id != packet_id
            or evidence.assessment_date != assessment_date
            or evidence.market != typed_market
        ):
            raise ValueError("v2_production_evidence_identity_mismatch")
    baselines = effective_prior_accepted(settings=settings)
    prior = tuple(
        baselines[ticker]
        for ticker in subjects
        if ticker in baselines and baselines[ticker].market == typed_market
    )
    return AcceptedV2ProductionContext(
        packet_id=packet_id,
        claim_id=claim_id,
        market=typed_market,
        assessment_date=assessment_date,
        source_packet_sha256=canonical_sha256(packet),
        selected_subjects=subjects,
        evidence_packets=tuple(by_ticker[ticker] for ticker in subjects),
        prior_accepted=prior,
        prepared_at=(prepared_at or datetime.now(UTC)).astimezone(UTC).isoformat(),
    )


def accepted_v2_production_prompt(
    context: AcceptedV2ProductionContext,
    *,
    subjects: Sequence[str] | None = None,
) -> str:
    selected = tuple(subjects or context.selected_subjects)
    packets = {row.ticker: row for row in context.evidence_packets}
    prior = {row.ticker: row for row in context.prior_accepted}
    if not selected or not set(selected).issubset(packets):
        raise ValueError("v2_production_prompt_subject_mismatch")
    payload = [
        {
            "canonical_evidence": compact_ai_context(packets[ticker]),
            "prior_accepted": (
                prior[ticker].model_dump(mode="json") if ticker in prior else None
            ),
        }
        for ticker in selected
    ]
    return (
        """You own the production-bound V2 analytical BUY/HOLD/SELL candidate and required accepted-decision adjudication. Use only the supplied canonical evidence. Do not browse, use later facts, calculate unregistered numbers, target prices, stops, order sizes, or fixed scores.

For every supplied ticker, emit exactly one PreconfirmationDecisionCandidate in candidates. Use VERY_HIGH reasoning_grade and concise natural Korean for every prose claim. Preserve exact complete evidence ref IDs. Distinguish factual safety from investment uncertainty. Evaluate evidence maturity, expectations, pricing requirement, Bear/Base/Bull scenarios, asymmetry, confirmation cost, and preconfirmation error cost without a weighted score. BUY before full confirmation is allowed only when the structured contract permits it. Confirmed business evidence can still be HOLD or SELL when expectations are demanding. Technical and market evidence may own timing, not long-horizon business asymmetry.

The prior accepted decision is continuity evidence, not a target distribution. Fresh evidence may justify a different candidate. If and only if candidate.decision differs from prior_accepted.accepted_decision, emit one AcceptedV2Adjudication for that ticker. In this legacy-compatible adjudication schema, v1_decision means prior accepted decision and v2_decision means the new candidate. KEEP_V1 means keep prior accepted; KEEP_V2 means accept the new candidate. NEEDS_REPAIR is allowed when no final accepted result is safe. Explain the decisive basis with canonical refs. If evidence is unchanged, do not change the top-level decision.

Change conditions are reassessment conditions, not automatic trades. Never describe a self transition: BUY must not be raised to BUY, HOLD must not be lowered to HOLD, and SELL must not be lowered to SELL. Refer to confidence/timing/risk when staying inside the same top-level decision.

Return strict JSON only. Copy packet_id, claim_id, market, and assessment_date exactly, set contract=v2-accepted-production-output-v1, and include no candidate or adjudication outside the supplied ticker set.

PRODUCTION_V2_CONTEXT:
"""
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
    )
def _production_message_quality(
    rendered: Sequence[RenderedProductionAcceptedDecision],
) -> dict[str, object]:
    errors: list[str] = []
    substantive: list[str] = []
    for row in rendered:
        if not row.validation.valid or len(row.text) > 2200:
            errors.append("production_render_invalid")
        for line in row.text.splitlines():
            normalized = re.sub(r"\s+", " ", line.strip().removeprefix("• "))
            if (
                len(normalized) >= 36
                and not normalized.startswith("분석 분류이며")
                and not normalized.startswith("판단 확신도:")
            ):
                substantive.append(normalized)
    repeated = [text for text, count in Counter(substantive).items() if count >= 2]
    if repeated:
        errors.append("cross_ticker_substantive_repetition")
    return {
        "contract": "v2-accepted-production-message-quality-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
        "message_count": len(rendered),
        "repeated_substantive_span_count": len(repeated),
        "numeric_claim_count": 0,
        "manual_numeric_count": 0,
        "unresolved_numeric_count": 0,
    }


def validate_accepted_v2_production_output(
    context: AcceptedV2ProductionContext,
    output: AcceptedV2ProductionBatchOutput,
    *,
    validated_at: datetime | None = None,
) -> AcceptedV2ProductionArtifact:
    if (
        output.packet_id,
        output.claim_id,
        output.market,
        output.assessment_date,
    ) != (
        context.packet_id,
        context.claim_id,
        context.market,
        context.assessment_date,
    ):
        raise ValueError("v2_production_output_identity_mismatch")
    packets = {row.ticker: row for row in context.evidence_packets}
    candidates = {row.ticker: row for row in output.candidates}
    if set(candidates) != set(context.selected_subjects) or len(candidates) != len(
        output.candidates
    ):
        raise ValueError("v2_production_candidate_scope_mismatch")
    for ticker, candidate in candidates.items():
        validation = validate_preconfirmation_candidate(packets[ticker], candidate)
        if not validation.valid:
            raise ValueError(
                "v2_production_candidate_invalid:"
                + ticker
                + ":"
                + ",".join(validation.errors)
            )
    prior = {row.ticker: row for row in context.prior_accepted}
    adjudications = {row.ticker: row for row in output.adjudications}
    if len(adjudications) != len(output.adjudications):
        raise ValueError("v2_production_duplicate_adjudication")
    changed = {
        ticker
        for ticker, candidate in candidates.items()
        if ticker in prior and candidate.decision != prior[ticker].accepted_decision
    }
    if set(adjudications) - changed:
        raise ValueError("v2_production_unrequired_adjudication")
    plans: list[AcceptedDecisionPlan] = []
    rendered: list[RenderedProductionAcceptedDecision] = []
    blocks: list[AcceptedV2ProductionBlock] = []
    for ticker in context.selected_subjects:
        packet = packets[ticker]
        candidate = candidates[ticker]
        baseline = prior.get(ticker)
        material_disagreement = ticker in changed
        plan = resolve_accepted_v2_decision(
            packet,
            candidate,
            v1_decision=(baseline.accepted_decision if baseline else candidate.decision),
            material_disagreement=material_disagreement,
            adjudication=adjudications.get(ticker),
        )
        plans.append(plan)
        if (
            baseline is not None
            and baseline.evidence_sha256 == packet.evidence_sha256
            and plan.status == AcceptedDecisionStatus.READY
            and plan.accepted_decision != baseline.accepted_decision
        ):
            raise ValueError(f"v2_production_same_evidence_unexplained_churn:{ticker}")
        if plan.status != AcceptedDecisionStatus.READY:
            continue
        validation = validate_accepted_v2_decision(packet, plan)
        if not validation.valid:
            raise ValueError(
                "v2_production_accepted_plan_invalid:"
                + ticker
                + ":"
                + ",".join(validation.errors)
            )
        rendered_row = render_accepted_v2_production(packet, plan)
        rendered.append(rendered_row)
        assert plan.accepted_decision is not None
        assert plan.accepted_decision_id is not None
        blocks.append(
            AcceptedV2ProductionBlock(
                ticker=ticker,
                decision=plan.accepted_decision,
                accepted_decision_id=plan.accepted_decision_id,
                text=rendered_row.text,
            )
        )
    quality = _production_message_quality(rendered)
    if quality["status"] != "PASS":
        raise ValueError("v2_production_message_quality_failed")
    ready_count = len(blocks)
    not_ready_count = len(context.selected_subjects) - ready_count
    return AcceptedV2ProductionArtifact(
        status="PASS" if not_ready_count == 0 else "PARTIAL_SAFE",
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        source_packet_sha256=context.source_packet_sha256,
        selected_subjects=context.selected_subjects,
        evidence_packets=context.evidence_packets,
        candidates=tuple(candidates[ticker] for ticker in context.selected_subjects),
        accepted_plans=tuple(plans),
        blocks=tuple(blocks),
        ready_count=ready_count,
        not_ready_count=not_ready_count,
        message_quality=quality,
        validated_at=(validated_at or datetime.now(UTC)).astimezone(UTC).isoformat(),
    )


def load_accepted_v2_production_artifact(
    path: Path,
    *,
    packet: Mapping[str, object],
    claim_id: str,
) -> AcceptedV2ProductionArtifact:
    artifact = AcceptedV2ProductionArtifact.model_validate_json(
        path.read_text(encoding="utf-8")
    )
    subjects = tuple(
        str(row.get("ticker") or "").upper()
        for row in packet.get("stocks") or ()
        if isinstance(row, Mapping)
    )
    if (
        artifact.packet_id != str(packet.get("packet_id") or "")
        or artifact.claim_id != claim_id
        or artifact.market != str(packet.get("market") or "")
        or artifact.assessment_date != str(packet.get("assessment_date") or "")
        or artifact.source_packet_sha256 != canonical_sha256(packet)
        or artifact.selected_subjects != subjects
    ):
        raise ValueError("v2_production_artifact_freshness_or_scope_mismatch")
    packets = {row.ticker: row for row in artifact.evidence_packets}
    plans = {row.ticker: row for row in artifact.accepted_plans}
    blocks = {row.ticker: row for row in artifact.blocks}
    if set(packets) != set(subjects) or set(plans) != set(subjects):
        raise ValueError("v2_production_artifact_subject_mismatch")
    for ticker, plan in plans.items():
        if plan.status != AcceptedDecisionStatus.READY:
            if ticker in blocks:
                raise ValueError("v2_production_not_ready_block_visible")
            continue
        expected = render_accepted_v2_production(packets[ticker], plan)
        block = blocks.get(ticker)
        if (
            block is None
            or block.decision != plan.accepted_decision
            or block.accepted_decision_id != plan.accepted_decision_id
            or block.text != expected.text
        ):
            raise ValueError("v2_production_artifact_block_mismatch")
    return artifact


def advance_accepted_v2_state(
    artifact: AcceptedV2ProductionArtifact,
    *,
    settings: Settings | None = None,
    updated_at: datetime | None = None,
) -> Path:
    existing = load_accepted_v2_state(settings=settings)
    entries = {row.ticker: row for row in (existing.entries if existing else ())}
    evidence = {row.ticker: row for row in artifact.evidence_packets}
    timestamp = (updated_at or datetime.now(UTC)).astimezone(UTC).isoformat()
    for plan in artifact.accepted_plans:
        if plan.status != AcceptedDecisionStatus.READY:
            continue
        entries[plan.ticker] = AcceptedV2ProductionStateEntry(
            ticker=plan.ticker,
            market=artifact.market,
            evidence_sha256=evidence[plan.ticker].evidence_sha256,
            accepted_plan=plan,
            source_packet_id=artifact.packet_id,
            assessment_date=artifact.assessment_date,
            updated_at=timestamp,
        )
    return write_accepted_v2_state(
        AcceptedV2ProductionState(
            entries=tuple(entries[ticker] for ticker in sorted(entries))
        ),
        settings=settings,
    )


def accepted_v2_runtime_preconditions(
    *, settings: Settings | None = None
) -> dict[str, object]:
    current = settings or get_settings()
    checks = {
        "visible_engine_v2_accepted": current.visible_stock_decision_engine
        == "v2_accepted",
        "v2_production_enabled": current.v2_production_enabled,
        "full_coverage_target": current.v2_full_monitored_stock_coverage_target,
        "v1_rollback_available": current.v1_decision_rollback_available,
        "migration_baseline_available": migration_baseline_path().exists(),
    }
    return {
        "contract": CONTRACT_VERSION,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "raw_candidate_visible": 0,
    }
