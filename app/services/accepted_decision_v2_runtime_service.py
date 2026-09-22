from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import Field

from app.config import Settings, get_settings
from app.services.accepted_decision_v2_service import (
    AcceptedDecisionFrozenCoreNumericScope,
    AcceptedDecisionPlan,
    AcceptedDecisionStatus,
    AcceptedV2Adjudication,
    RenderedProductionAcceptedDecision,
    render_accepted_v2_production,
    resolve_accepted_v2_decision,
    validate_accepted_v2_decision,
)
from app.services.production_validation_policy_service import (
    RepetitionClass,
    classify_repeated_span,
)
from app.services.cross_market_decision_engine_service import (
    Confidence,
    Decision,
    DecisionEvidencePacket,
    EvidenceClaim,
    FrozenModel,
    compact_ai_context,
)
from app.services.directional_balance_service import (
    DirectionalBalance,
    directional_balance_matches_decision,
)
from app.services.directional_balance_variance_service import (
    requires_directional_balance_adjudication,
)
from app.services.decision_canary_service import canonical_sha256, strict_json_schema
from app.services.preconfirmation_decision_v2_service import (
    PRECONFIRMATION_BUY_STAGE2_PROMPT_RULE,
    STAGE2_FROZEN_CORE_OWNERSHIP_CONTRACT,
    PreconfirmationDecisionCandidate,
    PreconfirmationDecisionCandidateV2,
    PreconfirmationValidationResult,
    preconfirmation_stage2_field_ownership_inventory,
    validate_preconfirmation_candidate,
    validate_preconfirmation_stage2_owned_semantics,
)
from app.services.expectation_valuation_interaction_service import (
    ExpectationValuationInteraction,
    duplicate_directional_anchor_errors,
    interaction_from_packet,
)
from app.services.evidence_maturity_pricing_service import (
    concrete_evidence_date,
    project_maturity_provenance,
)
from app.services.stage2_maturity_polarity_adapter_service import (
    ATOMIC_IDENTITY_CONTRACT,
    CONTRACT_VERSION as MATURITY_POLARITY_ADAPTER_CONTRACT,
    MaturityAtomicClaim,
    maturity_atomic_assignment_errors,
    stage2_maturity_atomic_claim_catalog,
)
from app.services.three_axis_decision_service import HolderDecisionAxis


CONTRACT_VERSION = "v2-accepted-production-runtime-v1"
OUTPUT_CONTRACT = "v2-accepted-production-output-v1"
OUTPUT_CONTRACT_V2 = "v2-accepted-production-output-v2"
STAGE2_MODEL_OUTPUT_CONTRACT_V2 = "v2-accepted-stage2-model-output-v2"
STAGE2_MODEL_OUTPUT_CONTRACT_V3 = "v2-accepted-stage2-model-output-v3"
STAGE2_MODEL_OUTPUT_CONTRACT = "v2-accepted-stage2-model-output-v4"
STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT = (
    "stage2-maturity-as-of-deterministic-v1"
)
STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT = (
    "stage2-maturity-as-of-deterministic-v2"
)
STAGE2_MATURITY_AS_OF_SEMANTICS = (
    "LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE"
)
STAGE2_MATURITY_AS_OF_AGGREGATION = "MAX_CONCRETE_OWNED_DATES"
ARTIFACT_CONTRACT = "v2-accepted-production-artifact-v1"
ARTIFACT_CONTRACT_V2 = "v2-accepted-production-artifact-v2"
STATE_CONTRACT = "v2-accepted-production-state-v1"
RECEIPT_CONTRACT = "v2-accepted-production-receipt-v1"
REASONING_MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "xhigh"
FUNDAMENTAL_CORE_CONTRACT = "v2-accepted-fundamental-core-v1"
FUNDAMENTAL_CORE_EXACT_REF_CONTRACT = "fundamental-core-exact-ref-fidelity-v1"
EXACT_REF_FIDELITY_CONTRACT = "model-output-exact-ref-fidelity-v1"
STAGE2_EXACT_REF_CONTRACT = "stage2-exact-ref-fidelity-v1"
FUNDAMENTAL_CORE_BATCH_IDENTITY_CONTRACT = (
    "fundamental-core-batch-identity-v1"
)


class AcceptedV2EvidenceOwnership(FrozenModel):
    ticker: str
    core_ref_ids: tuple[str, ...]
    timing_ref_ids: tuple[str, ...]
    expectation_valuation: ExpectationValuationInteraction


class AcceptedV2FundamentalCoreCandidate(FrozenModel):
    ticker: str
    decision: Decision
    directional_balance: DirectionalBalance
    buy_drivers: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=3)
    sell_drivers: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=3)
    balance_summary: str = Field(min_length=1, max_length=500)
    confidence: Confidence
    decisive_reason: EvidenceClaim
    holder_axis: HolderDecisionAxis


class AcceptedV2FundamentalCoreBatch(FrozenModel):
    contract: Literal["v2-accepted-fundamental-core-v1"] = FUNDAMENTAL_CORE_CONTRACT
    packet_id: str
    claim_id: str
    market: Literal["kr", "us"]
    assessment_date: str
    cores: tuple[AcceptedV2FundamentalCoreCandidate, ...] = Field(
        min_length=1, max_length=20
    )


def accepted_v2_maturity_atomic_claim_catalog(
    core: AcceptedV2FundamentalCoreCandidate,
) -> tuple[MaturityAtomicClaim, ...]:
    return stage2_maturity_atomic_claim_catalog(
        ticker=core.ticker,
        buy_drivers=core.buy_drivers,
        sell_drivers=core.sell_drivers,
    )


def accepted_v2_maturity_atomic_claim_catalog_manifest(
    fundamental_cores: Sequence[AcceptedV2FundamentalCoreCandidate] | None = None,
) -> dict[str, object]:
    tickers = tuple(core.ticker for core in fundamental_cores)
    if not tickers or len(tickers) != len(set(tickers)):
        raise ValueError("v2_maturity_atomic_claim_core_scope_invalid")
    rows = tuple(
        claim
        for core in fundamental_cores
        for claim in accepted_v2_maturity_atomic_claim_catalog(core)
    )
    payload = [
        {
            **row.model_dump(mode="json"),
            "parent_source_refs": list(row.parent_source_refs),
        }
        for row in rows
    ]
    return {
        "contract": MATURITY_POLARITY_ADAPTER_CONTRACT,
        "atomic_identity_contract": ATOMIC_IDENTITY_CONTRACT,
        "subjects": list(tickers),
        "claim_catalog_hash": canonical_sha256(payload),
        "claim_count": len(rows),
        "allowed_claim_refs": [row.claim_ref for row in rows],
        "claims": payload,
    }


def validate_accepted_v2_fundamental_core_batch_scope(
    batch: AcceptedV2FundamentalCoreBatch,
    context: AcceptedV2ProductionContext,
    *,
    subjects: Sequence[str],
) -> tuple[str, ...]:
    expected = tuple(subjects)
    returned = tuple(row.ticker for row in batch.cores)
    errors: list[str] = []
    if batch.packet_id != context.packet_id:
        errors.append("packet_id_mismatch")
    if batch.claim_id != context.claim_id:
        errors.append("claim_id_mismatch")
    if batch.market != context.market:
        errors.append("market_mismatch")
    if batch.assessment_date != context.assessment_date:
        errors.append("assessment_date_mismatch")
    if len(returned) != len(expected):
        errors.append(
            f"cardinality_mismatch:expected={len(expected)}:returned={len(returned)}"
        )
    counts = Counter(returned)
    errors.extend(
        f"duplicate_ticker:{ticker}"
        for ticker, count in sorted(counts.items())
        if count > 1
    )
    expected_set = set(expected)
    returned_set = set(returned)
    errors.extend(f"missing_ticker:{ticker}" for ticker in expected if ticker not in returned_set)
    errors.extend(
        f"extra_ticker:{ticker}" for ticker in returned if ticker not in expected_set
    )
    return tuple(errors)


class AcceptedV2ProductionBaseline(FrozenModel):
    ticker: str
    market: Literal["kr", "us"]
    accepted_decision: Decision
    evidence_sha256: str
    accepted_decision_id: str
    source: str
    accepted_directional_balance: DirectionalBalance | None = None
    accepted_buy_drivers: tuple[EvidenceClaim, ...] = ()
    accepted_sell_drivers: tuple[EvidenceClaim, ...] = ()
    accepted_balance_summary: str | None = None


class AcceptedV2ProductionContext(FrozenModel):
    contract: Literal["v2-accepted-production-runtime-v1"] = CONTRACT_VERSION
    packet_id: str
    claim_id: str
    market: Literal["kr", "us"]
    assessment_date: str
    source_packet_sha256: str
    selected_subjects: tuple[str, ...] = Field(min_length=1, max_length=20)
    evidence_packets: tuple[DecisionEvidencePacket, ...] = Field(min_length=1, max_length=20)
    evidence_ownership: tuple[AcceptedV2EvidenceOwnership, ...] = Field(
        min_length=1, max_length=20
    )
    prior_accepted: tuple[AcceptedV2ProductionBaseline, ...] = Field(default=(), max_length=20)
    prepared_at: str


def accepted_v2_fundamental_core_batch_identity_manifest(
    context: AcceptedV2ProductionContext,
    *,
    subjects: Sequence[str] | None = None,
) -> dict[str, object]:
    selected = tuple(subjects or context.selected_subjects)
    if (
        not selected
        or len(set(selected)) != len(selected)
        or not set(selected).issubset(context.selected_subjects)
    ):
        raise ValueError("v2_fundamental_core_identity_subject_mismatch")
    identity = {
        "contract": FUNDAMENTAL_CORE_CONTRACT,
        "packet_id": context.packet_id,
        "claim_id": context.claim_id,
        "market": context.market,
        "assessment_date": context.assessment_date,
    }
    contract_payload = {
        "contract": FUNDAMENTAL_CORE_BATCH_IDENTITY_CONTRACT,
        "identity": identity,
        "expected_subject_count": len(selected),
        "expected_tickers": list(selected),
    }
    return {
        **contract_payload,
        "ticker_domain_hash": canonical_sha256(list(selected)),
        "identity_contract_hash": canonical_sha256(contract_payload),
    }


class AcceptedV2ProductionBatchOutput(FrozenModel):
    contract: Literal["v2-accepted-production-output-v1"] = OUTPUT_CONTRACT
    packet_id: str
    claim_id: str
    market: Literal["kr", "us"]
    assessment_date: str
    fundamental_cores: tuple[AcceptedV2FundamentalCoreCandidate, ...] = Field(
        min_length=1, max_length=20
    )
    candidates: tuple[PreconfirmationDecisionCandidate, ...] = Field(min_length=1, max_length=20)
    adjudications: tuple[AcceptedV2Adjudication, ...] = Field(default=(), max_length=20)


class AcceptedV2ProductionBatchOutputV2(FrozenModel):
    contract: Literal["v2-accepted-production-output-v2"] = OUTPUT_CONTRACT_V2
    packet_id: str
    claim_id: str
    market: Literal["kr", "us"]
    assessment_date: str
    fundamental_cores: tuple[AcceptedV2FundamentalCoreCandidate, ...] = Field(
        min_length=1, max_length=20
    )
    candidates: tuple[PreconfirmationDecisionCandidateV2, ...] = Field(
        min_length=1, max_length=20
    )
    adjudications: tuple[AcceptedV2Adjudication, ...] = Field(default=(), max_length=20)


class Stage2MaturityAsOfMaterializationError(ValueError):
    pass


class AcceptedV2ProductionBlock(FrozenModel):
    ticker: str
    decision: Decision
    accepted_decision_id: str
    buy_balance: float | None = None
    sell_balance: float | None = None
    new_buyer_stance: Literal["ATTRACTIVE", "WAIT", "AVOID"] | None = None
    holder_stance: Literal["HOLDABLE", "REVIEW", "REDUCE"] | None = None
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
    evidence_ownership: tuple[AcceptedV2EvidenceOwnership, ...] = Field(
        min_length=1, max_length=20
    )
    fundamental_cores: tuple[AcceptedV2FundamentalCoreCandidate, ...] = Field(
        min_length=1, max_length=20
    )
    candidates: tuple[PreconfirmationDecisionCandidate, ...] = Field(min_length=1, max_length=20)
    accepted_plans: tuple[AcceptedDecisionPlan, ...] = Field(min_length=1, max_length=20)
    blocks: tuple[AcceptedV2ProductionBlock, ...] = Field(default=(), max_length=20)
    ready_count: int
    not_ready_count: int
    message_quality: dict[str, object]
    decision_consistency: dict[str, object] = Field(default_factory=dict)
    validated_at: str


class AcceptedV2ProductionArtifactV2(AcceptedV2ProductionArtifact):
    contract: Literal["v2-accepted-production-artifact-v2"] = ARTIFACT_CONTRACT_V2
    candidates: tuple[PreconfirmationDecisionCandidateV2, ...] = Field(
        min_length=1, max_length=20
    )


def parse_accepted_v2_production_batch_output(
    payload: Mapping[str, object],
) -> AcceptedV2ProductionBatchOutput | AcceptedV2ProductionBatchOutputV2:
    contract = payload.get("contract")
    if contract == OUTPUT_CONTRACT:
        return AcceptedV2ProductionBatchOutput.model_validate(payload)
    if contract == OUTPUT_CONTRACT_V2:
        return AcceptedV2ProductionBatchOutputV2.model_validate(payload)
    raise ValueError("unsupported_accepted_v2_output_contract")


def parse_accepted_v2_production_artifact(
    payload: Mapping[str, object],
) -> AcceptedV2ProductionArtifact | AcceptedV2ProductionArtifactV2:
    contract = payload.get("contract")
    if contract == ARTIFACT_CONTRACT:
        return AcceptedV2ProductionArtifact.model_validate(payload)
    if contract == ARTIFACT_CONTRACT_V2:
        return AcceptedV2ProductionArtifactV2.model_validate(payload)
    raise ValueError("unsupported_accepted_v2_artifact_contract")


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
        "core_schema": parent.parent
        / "claims"
        / f"{claim_stem}.decision-v2-core-schema.json",
        "core_prompt": parent.parent
        / "claims"
        / f"{claim_stem}.decision-v2-core-prompt.txt",
        "core_temp": parent / f"{claim_stem}.decision-v2-core.json.tmp",
        "core_log": parent.parent / "claims" / f"{claim_stem}.decision-v2-core-cli.log",
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


def load_accepted_v2_state(*, settings: Settings | None = None) -> AcceptedV2ProductionState | None:
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
                accepted_directional_balance=plan.accepted_directional_balance,
                accepted_buy_drivers=plan.accepted_buy_drivers,
                accepted_sell_drivers=plan.accepted_sell_drivers,
                accepted_balance_summary=plan.accepted_balance_summary,
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
    # This service is imported by onboarding initialization, while the ownership
    # service reaches back through AI review. Resolve it only when building a
    # context so module import order remains acyclic.
    from app.services.direction_timing_ownership_service import (
        build_owned_evidence_packet,
    )

    market = str(packet.get("market") or "").lower()
    if market not in {"kr", "us"}:
        raise ValueError("v2_production_market_invalid")
    typed_market: Literal["kr", "us"] = "kr" if market == "kr" else "us"
    stocks = [row for row in packet.get("stocks") or () if isinstance(row, Mapping)]
    subjects = tuple(str(row.get("ticker") or "").upper() for row in stocks)
    if not subjects or len(subjects) != len(set(subjects)):
        raise ValueError("v2_production_subject_inventory_invalid")
    by_ticker = {row.ticker: row for row in evidence_packets}
    stocks_by_ticker = {
        str(row.get("ticker") or "").upper(): row
        for row in stocks
    }
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
    ownership: list[AcceptedV2EvidenceOwnership] = []
    for ticker in subjects:
        owned = build_owned_evidence_packet(
            by_ticker[ticker],
            stock=stocks_by_ticker[ticker],
        )
        ownership.append(
            AcceptedV2EvidenceOwnership(
                ticker=ticker,
                core_ref_ids=tuple(sorted(owned.core_refs)),
                timing_ref_ids=tuple(sorted(owned.timing_refs)),
                expectation_valuation=interaction_from_packet(by_ticker[ticker]),
            )
        )
    return AcceptedV2ProductionContext(
        packet_id=packet_id,
        claim_id=claim_id,
        market=typed_market,
        assessment_date=assessment_date,
        source_packet_sha256=canonical_sha256(packet),
        selected_subjects=subjects,
        evidence_packets=tuple(by_ticker[ticker] for ticker in subjects),
        evidence_ownership=tuple(ownership),
        prior_accepted=prior,
        prepared_at=(prepared_at or datetime.now(UTC)).astimezone(UTC).isoformat(),
    )


def accepted_v2_fundamental_core_sha256(
    core: AcceptedV2FundamentalCoreCandidate,
) -> str:
    return canonical_sha256(core.model_dump(mode="json"))


def accepted_v2_fundamental_core_from_candidate(
    candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
) -> AcceptedV2FundamentalCoreCandidate:
    return AcceptedV2FundamentalCoreCandidate(
        ticker=candidate.ticker,
        decision=candidate.decision,
        directional_balance=candidate.directional_balance,
        buy_drivers=candidate.buy_drivers,
        sell_drivers=candidate.sell_drivers,
        balance_summary=candidate.balance_summary,
        confidence=candidate.confidence,
        decisive_reason=candidate.decisive_reason,
        holder_axis=candidate.holder_axis,
    )


def _claim_ref_set(claims: Sequence[EvidenceClaim]) -> set[str]:
    return {
        ref_id
        for claim in claims
        for ref_id in claim.evidence_refs
    }


def validate_accepted_v2_fundamental_core(
    core: AcceptedV2FundamentalCoreCandidate,
    ownership: AcceptedV2EvidenceOwnership,
) -> tuple[str, ...]:
    errors: list[str] = []
    if core.ticker != ownership.ticker:
        errors.append("fundamental_core_ticker_mismatch")
    if not directional_balance_matches_decision(core.directional_balance, core.decision):
        errors.append("fundamental_core_directional_balance_mismatch")
    try:
        accepted_v2_maturity_atomic_claim_catalog(core)
    except ValueError as exc:
        errors.append(f"fundamental_core_atomic_claim_identity_invalid:{exc}")
    core_refs = _claim_ref_set(
        (
            *core.buy_drivers,
            *core.sell_drivers,
            core.decisive_reason,
            core.holder_axis.reason,
        )
    )
    allowed = set(ownership.core_ref_ids)
    timing = sorted(core_refs & set(ownership.timing_ref_ids))
    outside = sorted(core_refs - allowed)
    errors.extend(f"price_timing_in_fundamental_core:{ref_id}" for ref_id in timing)
    errors.extend(f"noncore_ref_in_fundamental_core:{ref_id}" for ref_id in outside)
    errors.extend(
        duplicate_directional_anchor_errors(
            interaction=ownership.expectation_valuation,
            driver_ref_groups=tuple(
                claim.evidence_refs for claim in (*core.buy_drivers, *core.sell_drivers)
            ),
        )
    )
    return tuple(dict.fromkeys(errors))


def validate_accepted_v2_candidate_ownership(
    candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
    core: AcceptedV2FundamentalCoreCandidate,
    ownership: AcceptedV2EvidenceOwnership,
) -> tuple[str, ...]:
    errors = list(validate_accepted_v2_fundamental_core(core, ownership))
    projected = accepted_v2_fundamental_core_from_candidate(candidate)
    expected_sha = accepted_v2_fundamental_core_sha256(core)
    if candidate.fundamental_core_sha256 != expected_sha:
        errors.append("fundamental_core_fingerprint_mismatch")
    if projected != core:
        errors.append("price_timing_stage_mutated_fundamental_core")
    known = set(ownership.core_ref_ids) | set(ownership.timing_ref_ids)
    unknown_new_buyer = sorted(set(candidate.new_buyer_axis.reason.evidence_refs) - known)
    errors.extend(
        f"new_buyer_ref_outside_owned_evidence:{ref_id}"
        for ref_id in unknown_new_buyer
    )
    holder_timing = sorted(
        set(candidate.holder_axis.reason.evidence_refs) & set(ownership.timing_ref_ids)
    )
    errors.extend(f"price_timing_in_holder_anchor:{ref_id}" for ref_id in holder_timing)
    return tuple(dict.fromkeys(errors))


def accepted_v2_stage2_validation_scope_manifest() -> dict[str, object]:
    fields = preconfirmation_stage2_field_ownership_inventory()
    return {
        "contract": STAGE2_FROZEN_CORE_OWNERSHIP_CONTRACT,
        "trust_preconditions": [
            "fundamental_core_schema_valid",
            "fundamental_core_canonical_semantic_valid",
            "fundamental_core_sha256_exact",
            "frozen_core_fields_exact_copy",
            "no_core_mutation",
        ],
        "claim_language_scope_after_trust": "STAGE2_OWNED_FIELDS_ONLY",
        "unsupported_metric_scope_after_trust": "STAGE2_OWNED_FIELDS_ONLY",
        "fields": list(fields),
    }


def validate_accepted_v2_stage2_candidate(
    packet: DecisionEvidencePacket,
    candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
    core: AcceptedV2FundamentalCoreCandidate,
    ownership: AcceptedV2EvidenceOwnership,
) -> PreconfirmationValidationResult:
    """Validate core identity first, then scope Stage-2 prose rules to Stage-2 claims."""
    ownership_errors = validate_accepted_v2_candidate_ownership(
        candidate,
        core,
        ownership,
    )
    semantic_validation = (
        validate_preconfirmation_candidate(packet, candidate)
        if ownership_errors
        else validate_preconfirmation_stage2_owned_semantics(packet, candidate)
    )
    maturity_errors = validate_accepted_v2_maturity_atomic_identity(candidate, core)
    errors = tuple(
        dict.fromkeys((*ownership_errors, *semantic_validation.errors, *maturity_errors))
    )
    return semantic_validation.model_copy(update={"valid": not errors, "errors": errors})


def validate_accepted_v2_maturity_atomic_identity(
    candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
    core: AcceptedV2FundamentalCoreCandidate,
) -> tuple[str, ...]:
    return maturity_atomic_assignment_errors(
        candidate.driver_maturity,
        catalog=accepted_v2_maturity_atomic_claim_catalog(core),
    )


def _compact_owned_evidence(
    packet: DecisionEvidencePacket,
    ref_ids: Sequence[str],
) -> dict[str, object]:
    allowed = {ref_id for ref_id in ref_ids if not ref_id.startswith("technical-feature:")}
    return compact_ai_context(
        packet.model_copy(
            update={"evidence": tuple(row for row in packet.evidence if row.ref_id in allowed)}
        )
    )


def _compact_stage2_owned_evidence(
    packet: DecisionEvidencePacket,
    ref_ids: Sequence[str],
) -> dict[str, object]:
    compact = _compact_owned_evidence(packet, ref_ids)
    rows = compact.get("evidence")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            resolved = concrete_evidence_date(
                str(row["as_of"]) if row.get("as_of") is not None else None
            )
            row["resolved_as_of_date"] = resolved.isoformat() if resolved else None
    return compact


def accepted_v2_fundamental_core_ref_catalog(
    context: AcceptedV2ProductionContext,
    *,
    subjects: Sequence[str] | None = None,
) -> tuple[str, ...]:
    selected = tuple(subjects or context.selected_subjects)
    packets = {row.ticker: row for row in context.evidence_packets}
    ownership = {row.ticker: row for row in context.evidence_ownership}
    if (
        not selected
        or not set(selected).issubset(packets)
        or not set(selected).issubset(ownership)
    ):
        raise ValueError("v2_fundamental_core_ref_catalog_subject_mismatch")

    visible_refs: set[str] = set()
    for ticker in selected:
        owned_core_refs = set(ownership[ticker].core_ref_ids)
        visible_refs.update(
            row.ref_id
            for row in packets[ticker].evidence
            if row.ref_id in owned_core_refs
            and not row.ref_id.startswith("technical-feature:")
        )
    return tuple(sorted(visible_refs))


def accepted_v2_fundamental_core_ref_catalog_manifest(
    context: AcceptedV2ProductionContext,
    *,
    subjects: Sequence[str] | None = None,
) -> dict[str, object]:
    selected = tuple(subjects or context.selected_subjects)
    refs = accepted_v2_fundamental_core_ref_catalog(context, subjects=selected)
    packets = {row.ticker: row for row in context.evidence_packets}
    ownership = {row.ticker: row for row in context.evidence_ownership}
    source_condition_refs: set[str] = set()
    leaf_refs: set[str] = set()

    def collect_leaf_refs(expression: object) -> None:
        if not hasattr(expression, "condition_id"):
            raise ValueError("v2_fundamental_core_source_condition_invalid")
        children = getattr(expression, "children", None)
        if children is None:
            leaf_refs.add(str(getattr(expression, "condition_id")))
            return
        for child in children:
            collect_leaf_refs(child)

    for ticker in selected:
        owned_core_refs = set(ownership[ticker].core_ref_ids)
        for row in packets[ticker].evidence:
            if (
                row.ref_id not in owned_core_refs
                or row.ref_id.startswith("technical-feature:")
                or row.logical_condition is None
            ):
                continue
            source_condition_refs.add(row.logical_condition.source_condition_ref)
            collect_leaf_refs(row.logical_condition.expression)

    ordered_source_condition_refs = tuple(sorted(source_condition_refs))
    ordered_leaf_refs = tuple(sorted(leaf_refs))
    catalog_hash = canonical_sha256(
        {
            "contract": FUNDAMENTAL_CORE_EXACT_REF_CONTRACT,
            "allowed_refs": refs,
            "allowed_source_condition_refs": ordered_source_condition_refs,
            "allowed_leaf_refs": ordered_leaf_refs,
        }
    )
    return {
        "contract": FUNDAMENTAL_CORE_EXACT_REF_CONTRACT,
        "packet_id": context.packet_id,
        "claim_id": context.claim_id,
        "market": context.market,
        "subjects": list(selected),
        "ref_catalog_hash": catalog_hash,
        "ref_catalog_count": len(refs),
        "allowed_refs": list(refs),
        "source_condition_ref_count": len(ordered_source_condition_refs),
        "allowed_source_condition_refs": list(ordered_source_condition_refs),
        "leaf_ref_count": len(ordered_leaf_refs),
        "allowed_leaf_refs": list(ordered_leaf_refs),
    }


def _exact_ref_output_schema(
    model_schema: dict[str, object],
    *,
    evidence_ref_fields: Sequence[tuple[str, str]],
    refs: Sequence[str],
    source_condition_refs: Sequence[str],
    leaf_refs: Sequence[str],
    error_prefix: str,
) -> dict[str, object]:
    schema = strict_json_schema(model_schema)
    if not isinstance(schema, dict):
        raise ValueError(f"{error_prefix}_schema_invalid")

    for definition, property_name in evidence_ref_fields:
        try:
            evidence_refs = schema["$defs"][definition]["properties"][property_name]
            items = evidence_refs["items"]
        except (KeyError, TypeError) as exc:
            raise ValueError(f"{error_prefix}_ref_schema_path_missing") from exc
        if not isinstance(evidence_refs, dict) or evidence_refs.get("type") != "array":
            raise ValueError(f"{error_prefix}_ref_schema_not_array")
        if not isinstance(items, dict) or items.get("type") != "string":
            raise ValueError(f"{error_prefix}_ref_schema_item_not_string")
        items["enum"] = list(refs)

    try:
        logical_condition = schema["$defs"]["EvidenceClaim"]["properties"][
            "logical_condition"
        ]
        source_condition_ref = schema["$defs"]["ClaimLogicalCondition"][
            "properties"
        ]["source_condition_ref"]
        leaf_ref = schema["$defs"]["ClaimLogicalLeaf"]["properties"]["leaf_ref"]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"{error_prefix}_logical_ref_schema_path_missing") from exc
    if not isinstance(logical_condition, dict):
        raise ValueError(f"{error_prefix}_logical_condition_schema_invalid")
    if not source_condition_refs and not leaf_refs:
        schema["$defs"]["EvidenceClaim"]["properties"]["logical_condition"] = {
            "type": "null"
        }
    else:
        if not source_condition_refs or not leaf_refs:
            raise ValueError(f"{error_prefix}_logical_ref_catalog_incomplete")
        if (
            not isinstance(source_condition_ref, dict)
            or source_condition_ref.get("type") != "string"
            or not isinstance(leaf_ref, dict)
            or leaf_ref.get("type") != "string"
        ):
            raise ValueError(f"{error_prefix}_logical_ref_schema_not_string")
        source_condition_ref["enum"] = list(source_condition_refs)
        leaf_ref["enum"] = list(leaf_refs)
    return schema


def accepted_v2_fundamental_core_output_schema(
    context: AcceptedV2ProductionContext,
    *,
    subjects: Sequence[str] | None = None,
) -> dict[str, object]:
    identity_manifest = accepted_v2_fundamental_core_batch_identity_manifest(
        context,
        subjects=subjects,
    )
    selected = tuple(str(value) for value in identity_manifest["expected_tickers"])
    manifest = accepted_v2_fundamental_core_ref_catalog_manifest(
        context,
        subjects=selected,
    )
    refs = manifest["allowed_refs"]
    source_condition_refs = manifest["allowed_source_condition_refs"]
    leaf_refs = manifest["allowed_leaf_refs"]
    if not isinstance(refs, list) or not refs:
        raise ValueError("v2_fundamental_core_ref_catalog_empty")

    schema = _exact_ref_output_schema(
        AcceptedV2FundamentalCoreBatch.model_json_schema(),
        evidence_ref_fields=(("EvidenceClaim", "evidence_refs"),),
        refs=refs,
        source_condition_refs=source_condition_refs,
        leaf_refs=leaf_refs,
        error_prefix="v2_fundamental_core",
    )
    try:
        properties = schema["properties"]
        definitions = schema["$defs"]
        cores = properties["cores"]
        ticker = definitions["AcceptedV2FundamentalCoreCandidate"]["properties"][
            "ticker"
        ]
    except (KeyError, TypeError) as exc:
        raise ValueError("v2_fundamental_core_identity_schema_path_missing") from exc
    for field_name, value in (
        ("contract", FUNDAMENTAL_CORE_CONTRACT),
        ("packet_id", context.packet_id),
        ("claim_id", context.claim_id),
        ("market", context.market),
        ("assessment_date", context.assessment_date),
    ):
        field = properties[field_name]
        if not isinstance(field, dict):
            raise ValueError(f"v2_fundamental_core_identity_schema_invalid:{field_name}")
        field["const"] = value
    if not isinstance(cores, dict) or cores.get("type") != "array":
        raise ValueError("v2_fundamental_core_cores_schema_invalid")
    cores["minItems"] = len(selected)
    cores["maxItems"] = len(selected)
    if not isinstance(ticker, dict) or ticker.get("type") != "string":
        raise ValueError("v2_fundamental_core_ticker_schema_invalid")
    ticker["enum"] = list(selected)
    return schema


def _collect_claim_logical_refs(
    claims: Sequence[EvidenceClaim],
    *,
    source_condition_refs: set[str],
    leaf_refs: set[str],
) -> None:
    def collect_expression(expression: object) -> None:
        children = getattr(expression, "children", None)
        if children is None:
            leaf_refs.add(str(getattr(expression, "leaf_ref")))
            return
        for child in children:
            collect_expression(child)

    for claim in claims:
        condition = claim.logical_condition
        if condition is None:
            continue
        source_condition_refs.add(condition.source_condition_ref)
        collect_expression(condition.expression)


def accepted_v2_stage2_ref_catalog_manifest(
    context: AcceptedV2ProductionContext,
    *,
    subjects: Sequence[str] | None = None,
    fundamental_cores: Sequence[AcceptedV2FundamentalCoreCandidate] | None = None,
) -> dict[str, object]:
    selected = tuple(subjects or context.selected_subjects)
    packets = {row.ticker: row for row in context.evidence_packets}
    ownership = {row.ticker: row for row in context.evidence_ownership}
    prior = {row.ticker: row for row in context.prior_accepted}
    if (
        not selected
        or not set(selected).issubset(packets)
        or not set(selected).issubset(ownership)
    ):
        raise ValueError("v2_stage2_ref_catalog_subject_mismatch")

    visible_refs: set[str] = set()
    maturity_ref_dates: dict[str, set[str]] = {}
    source_condition_refs: set[str] = set()
    leaf_refs: set[str] = set()

    def collect_source_expression(expression: object) -> None:
        children = getattr(expression, "children", None)
        if children is None:
            leaf_refs.add(str(getattr(expression, "condition_id")))
            return
        for child in children:
            collect_source_expression(child)

    for ticker in selected:
        visible_owned_refs = set(ownership[ticker].core_ref_ids) | set(
            ownership[ticker].timing_ref_ids
        )
        for row in packets[ticker].evidence:
            if row.ref_id not in visible_owned_refs or row.ref_id.startswith(
                "technical-feature:"
            ):
                continue
            visible_refs.add(row.ref_id)
            resolved_date = concrete_evidence_date(row.as_of)
            if resolved_date is not None:
                maturity_ref_dates.setdefault(row.ref_id, set()).add(
                    resolved_date.isoformat()
                )
            if row.logical_condition is not None:
                source_condition_refs.add(row.logical_condition.source_condition_ref)
                collect_source_expression(row.logical_condition.expression)
        baseline = prior.get(ticker)
        if baseline is not None:
            prior_claims = (*baseline.accepted_buy_drivers, *baseline.accepted_sell_drivers)
            visible_refs.update(_claim_ref_set(prior_claims))
            _collect_claim_logical_refs(
                prior_claims,
                source_condition_refs=source_condition_refs,
                leaf_refs=leaf_refs,
            )

    ordered_refs = tuple(sorted(visible_refs))
    ordered_maturity_ref_dates = {
        ref_id: sorted(maturity_ref_dates[ref_id])
        for ref_id in sorted(maturity_ref_dates)
        if ref_id in visible_refs
    }
    allowed_maturity_dates = tuple(
        sorted({value for values in ordered_maturity_ref_dates.values() for value in values})
    )
    ordered_source_condition_refs = tuple(sorted(source_condition_refs))
    ordered_leaf_refs = tuple(sorted(leaf_refs))
    atomic_manifest: dict[str, object] | None = None
    if fundamental_cores is not None:
        core_tickers = tuple(core.ticker for core in fundamental_cores)
        if core_tickers != selected:
            raise ValueError("v2_stage2_maturity_atomic_core_scope_mismatch")
        atomic_manifest = accepted_v2_maturity_atomic_claim_catalog_manifest(
            fundamental_cores
        )
    catalog_payload: dict[str, object] = {
        "contract": STAGE2_EXACT_REF_CONTRACT,
        "shared_contract": EXACT_REF_FIDELITY_CONTRACT,
        "allowed_refs": ordered_refs,
        "maturity_ref_dates": ordered_maturity_ref_dates,
        "allowed_source_condition_refs": ordered_source_condition_refs,
        "allowed_leaf_refs": ordered_leaf_refs,
    }
    if atomic_manifest is not None:
        catalog_payload["maturity_atomic_claim_catalog_hash"] = atomic_manifest[
            "claim_catalog_hash"
        ]
        catalog_payload["allowed_maturity_claim_refs"] = atomic_manifest[
            "allowed_claim_refs"
        ]
    catalog_hash = canonical_sha256(catalog_payload)
    return {
        "contract": STAGE2_EXACT_REF_CONTRACT,
        "shared_contract": EXACT_REF_FIDELITY_CONTRACT,
        "packet_id": context.packet_id,
        "claim_id": context.claim_id,
        "market": context.market,
        "subjects": list(selected),
        "ref_catalog_hash": catalog_hash,
        "ref_catalog_count": len(ordered_refs),
        "allowed_refs": list(ordered_refs),
        "maturity_date_catalog_hash": canonical_sha256(ordered_maturity_ref_dates),
        "maturity_date_count": len(allowed_maturity_dates),
        "allowed_maturity_dates": list(allowed_maturity_dates),
        "maturity_ref_dates": ordered_maturity_ref_dates,
        "source_condition_ref_count": len(ordered_source_condition_refs),
        "allowed_source_condition_refs": list(ordered_source_condition_refs),
        "leaf_ref_count": len(ordered_leaf_refs),
        "allowed_leaf_refs": list(ordered_leaf_refs),
        "maturity_polarity_adapter_contract": MATURITY_POLARITY_ADAPTER_CONTRACT,
        "maturity_atomic_identity_contract": ATOMIC_IDENTITY_CONTRACT,
        "maturity_atomic_claim_catalog_hash": (
            atomic_manifest["claim_catalog_hash"] if atomic_manifest is not None else None
        ),
        "maturity_atomic_claim_count": (
            atomic_manifest["claim_count"] if atomic_manifest is not None else 0
        ),
        "allowed_maturity_claim_refs": (
            atomic_manifest["allowed_claim_refs"] if atomic_manifest is not None else []
        ),
        "maturity_atomic_claims": (
            atomic_manifest["claims"] if atomic_manifest is not None else []
        ),
    }


def accepted_v2_stage2_output_schema(
    context: AcceptedV2ProductionContext,
    *,
    subjects: Sequence[str] | None = None,
    fundamental_cores: Sequence[AcceptedV2FundamentalCoreCandidate] | None = None,
) -> dict[str, object]:
    manifest = accepted_v2_stage2_ref_catalog_manifest(
        context,
        subjects=subjects,
        fundamental_cores=fundamental_cores,
    )
    refs = manifest["allowed_refs"]
    source_condition_refs = manifest["allowed_source_condition_refs"]
    leaf_refs = manifest["allowed_leaf_refs"]
    if not isinstance(refs, list) or not refs:
        raise ValueError("v2_stage2_ref_catalog_empty")
    if not isinstance(source_condition_refs, list) or not isinstance(leaf_refs, list):
        raise ValueError("v2_stage2_logical_ref_catalog_invalid")
    schema = _exact_ref_output_schema(
        AcceptedV2ProductionBatchOutput.model_json_schema(),
        evidence_ref_fields=(
            ("EvidenceClaim", "evidence_refs"),
            ("DriverEvidenceMaturity", "supporting_evidence_refs"),
            ("DriverEvidenceMaturity", "contradicting_evidence_refs"),
        ),
        refs=refs,
        source_condition_refs=source_condition_refs,
        leaf_refs=leaf_refs,
        error_prefix="v2_stage2",
    )
    selected = tuple(subjects or context.selected_subjects)
    try:
        properties = schema["properties"]
        definitions = schema["$defs"]
        maturity_definition = definitions["DriverEvidenceMaturity"]
        maturity_properties = maturity_definition["properties"]
        maturity_required = maturity_definition["required"]
    except (KeyError, TypeError) as exc:
        raise ValueError("v2_stage2_typed_schema_path_missing") from exc
    for field_name, value in (
        ("contract", STAGE2_MODEL_OUTPUT_CONTRACT),
        ("packet_id", context.packet_id),
        ("claim_id", context.claim_id),
        ("market", context.market),
        ("assessment_date", context.assessment_date),
    ):
        field = properties[field_name]
        if not isinstance(field, dict):
            raise ValueError(f"v2_stage2_identity_schema_invalid:{field_name}")
        field["const"] = value
    for definition in (
        "AcceptedV2Adjudication",
        "AcceptedV2FundamentalCoreCandidate",
        "PreconfirmationDecisionCandidate",
    ):
        ticker = definitions[definition]["properties"]["ticker"]
        if not isinstance(ticker, dict):
            raise ValueError(f"v2_stage2_ticker_schema_invalid:{definition}")
        ticker["enum"] = list(selected)
    if not isinstance(maturity_properties, dict) or not isinstance(
        maturity_required, list
    ):
        raise ValueError("v2_stage2_maturity_schema_invalid")
    for runtime_owned_field in (
        "supporting_evidence_refs",
        "contradicting_evidence_refs",
        "as_of",
    ):
        maturity_properties.pop(runtime_owned_field, None)
    maturity_definition["required"] = [
        value
        for value in maturity_required
        if value
        not in {
            "supporting_evidence_refs",
            "contradicting_evidence_refs",
            "as_of",
        }
    ]
    claim_refs = manifest["allowed_maturity_claim_refs"]
    if fundamental_cores is not None and (not isinstance(claim_refs, list) or not claim_refs):
        raise ValueError("v2_stage2_maturity_atomic_claim_catalog_empty")
    try:
        maturity_properties = definitions["DriverEvidenceMaturity"]["properties"]
        supporting_claim_refs = maturity_properties["supporting_claim_refs"]
        contradicting_claim_refs = maturity_properties["contradicting_claim_refs"]
    except (KeyError, TypeError) as exc:
        raise ValueError("v2_stage2_maturity_claim_schema_path_missing") from exc
    if not isinstance(supporting_claim_refs, dict) or not isinstance(
        contradicting_claim_refs, dict
    ):
        raise ValueError("v2_stage2_maturity_claim_schema_invalid")
    supporting_claim_refs["minItems"] = 1
    if isinstance(claim_refs, list) and claim_refs:
        for field in (supporting_claim_refs, contradicting_claim_refs):
            items = field.get("items")
            if not isinstance(items, dict) or items.get("type") != "string":
                raise ValueError("v2_stage2_maturity_claim_schema_invalid")
            items["enum"] = list(claim_refs)
    return schema


def _stage2_model_facing_candidate_payload(
    candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
) -> dict[str, object]:
    payload = candidate.model_dump(mode="json")
    rows = payload.get("driver_maturity")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                row.pop("supporting_evidence_refs", None)
                row.pop("contradicting_evidence_refs", None)
                row.pop("as_of", None)
                row.pop("provenance_status", None)
    return payload


def _stage2_model_facing_rejected_output(
    rejected_output: Mapping[str, object],
) -> dict[str, object]:
    payload = deepcopy(dict(rejected_output))
    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            rows = candidate.get("driver_maturity")
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, dict):
                        row.pop("supporting_evidence_refs", None)
                        row.pop("contradicting_evidence_refs", None)
                        row.pop("as_of", None)
                        row.pop("provenance_status", None)
    return payload


def materialize_accepted_v2_stage2_output(
    context: AcceptedV2ProductionContext,
    raw_output: Mapping[str, object],
    *,
    fundamental_cores: Sequence[AcceptedV2FundamentalCoreCandidate] | None = None,
    subjects: Sequence[str] | None = None,
    normalized_contract: str = STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT,
) -> AcceptedV2ProductionBatchOutput | AcceptedV2ProductionBatchOutputV2:
    """Materialize runtime-owned source refs and provenance into a typed contract."""
    if normalized_contract not in {
        STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT,
        STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT,
    }:
        raise Stage2MaturityAsOfMaterializationError(
            "unsupported_normalized_contract"
        )
    selected = tuple(subjects or context.selected_subjects)
    if (
        not selected
        or len(set(selected)) != len(selected)
        or not set(selected).issubset(context.selected_subjects)
    ):
        raise Stage2MaturityAsOfMaterializationError(
            "stage2_materialization_subject_scope_invalid"
        )
    payload = deepcopy(dict(raw_output))
    model_contract = payload.get("contract")
    if model_contract not in {
        STAGE2_MODEL_OUTPUT_CONTRACT_V2,
        STAGE2_MODEL_OUTPUT_CONTRACT_V3,
        STAGE2_MODEL_OUTPUT_CONTRACT,
    }:
        raise Stage2MaturityAsOfMaterializationError(
            "stage2_model_output_contract_mismatch"
        )
    runtime_owns_source_refs = model_contract in {
        STAGE2_MODEL_OUTPUT_CONTRACT_V3,
        STAGE2_MODEL_OUTPUT_CONTRACT,
    }
    trusted_cores = tuple(fundamental_cores or ())
    if runtime_owns_source_refs:
        if tuple(core.ticker for core in trusted_cores) != selected:
            raise Stage2MaturityAsOfMaterializationError(
                "stage2_materialization_fundamental_core_scope_mismatch"
            )
        trusted_core_payload = [core.model_dump(mode="json") for core in trusted_cores]
        if payload.get("fundamental_cores") != trusted_core_payload:
            raise Stage2MaturityAsOfMaterializationError(
                "stage2_materialization_fundamental_core_identity_mismatch"
            )
    for field_name, expected in (
        ("packet_id", context.packet_id),
        ("claim_id", context.claim_id),
        ("market", context.market),
        ("assessment_date", context.assessment_date),
    ):
        if payload.get(field_name) != expected:
            raise Stage2MaturityAsOfMaterializationError(
                f"stage2_materialization_identity_mismatch:{field_name}"
            )
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise Stage2MaturityAsOfMaterializationError(
            "stage2_materialization_candidates_invalid"
        )
    candidate_tickers = tuple(
        str(candidate.get("ticker"))
        for candidate in candidates
        if isinstance(candidate, dict)
    )
    if (
        len(candidate_tickers) != len(candidates)
        or len(set(candidate_tickers)) != len(candidate_tickers)
        or set(candidate_tickers) != set(selected)
    ):
        raise Stage2MaturityAsOfMaterializationError(
            "stage2_materialization_candidate_scope_mismatch"
        )

    packets = {packet.ticker: packet for packet in context.evidence_packets}
    ownership = {row.ticker: row for row in context.evidence_ownership}
    atomic_catalogs = (
        {
            core.ticker: accepted_v2_maturity_atomic_claim_catalog(core)
            for core in trusted_cores
        }
        if runtime_owns_source_refs
        else {}
    )
    atomic_claims_by_ref = {
        claim.claim_ref: claim
        for catalog in atomic_catalogs.values()
        for claim in catalog
    }
    assessment_date = concrete_evidence_date(context.assessment_date)
    if assessment_date is None:
        raise Stage2MaturityAsOfMaterializationError(
            "stage2_materialization_assessment_date_invalid"
        )
    for candidate_index, candidate in enumerate(candidates):
        assert isinstance(candidate, dict)
        ticker = str(candidate["ticker"])
        packet = packets.get(ticker)
        owned = ownership.get(ticker)
        if packet is None or owned is None:
            raise Stage2MaturityAsOfMaterializationError(
                f"stage2_materialization_ticker_context_missing:{ticker}"
            )
        visible_refs = {
            ref_id
            for ref_id in (*owned.core_ref_ids, *owned.timing_ref_ids)
            if not ref_id.startswith("technical-feature:")
        }
        evidence = {
            row.ref_id: row for row in packet.evidence if row.ref_id in visible_refs
        }
        rows = candidate.get("driver_maturity")
        if not isinstance(rows, list):
            raise Stage2MaturityAsOfMaterializationError(
                f"stage2_materialization_rows_invalid:{ticker}:{candidate_index}"
            )
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise Stage2MaturityAsOfMaterializationError(
                    f"stage2_materialization_row_invalid:{ticker}:{row_index}"
                )
            if "as_of" in row:
                raise Stage2MaturityAsOfMaterializationError(
                    f"stage2_model_authored_as_of_forbidden:{ticker}:{row_index}"
                )
            if "provenance_status" in row:
                raise Stage2MaturityAsOfMaterializationError(
                    f"stage2_model_authored_provenance_status_forbidden:"
                    f"{ticker}:{row_index}"
                )
            cited_refs: list[str] = []
            if runtime_owns_source_refs:
                for field_name in (
                    "supporting_evidence_refs",
                    "contradicting_evidence_refs",
                ):
                    if field_name in row:
                        raise Stage2MaturityAsOfMaterializationError(
                            f"stage2_model_authored_source_refs_forbidden:"
                            f"{ticker}:{row_index}:{field_name}"
                        )

                catalog_by_ref = {
                    claim.claim_ref: claim for claim in atomic_catalogs[ticker]
                }
                selected_claims: dict[str, tuple[str, ...]] = {}
                for side in ("supporting", "contradicting"):
                    field_name = f"{side}_claim_refs"
                    values = row.get(field_name)
                    if not isinstance(values, list) or any(
                        not isinstance(value, str) for value in values
                    ):
                        raise Stage2MaturityAsOfMaterializationError(
                            f"stage2_materialization_claim_ref_list_invalid:"
                            f"{ticker}:{row_index}:{field_name}"
                        )
                    claim_refs = tuple(values)
                    if side == "supporting" and not claim_refs:
                        raise Stage2MaturityAsOfMaterializationError(
                            f"stage2_materialization_supporting_claim_identity_missing:"
                            f"{ticker}:{row_index}"
                        )
                    if len(claim_refs) != len(set(claim_refs)):
                        raise Stage2MaturityAsOfMaterializationError(
                            f"stage2_materialization_duplicate_{side}_claim_ref:"
                            f"{ticker}:{row_index}"
                        )
                    for claim_ref in claim_refs:
                        claim = catalog_by_ref.get(claim_ref)
                        if claim is None:
                            foreign_claim = atomic_claims_by_ref.get(claim_ref)
                            if foreign_claim is not None:
                                raise Stage2MaturityAsOfMaterializationError(
                                    f"stage2_materialization_cross_ticker_claim_ref:"
                                    f"{ticker}:{row_index}:{claim_ref}"
                                )
                            raise Stage2MaturityAsOfMaterializationError(
                                f"stage2_materialization_unknown_ticker_local_claim_ref:"
                                f"{ticker}:{row_index}:{claim_ref}"
                            )
                        if claim.ticker != ticker:
                            raise Stage2MaturityAsOfMaterializationError(
                                f"stage2_materialization_cross_ticker_claim_ref:"
                                f"{ticker}:{row_index}:{claim_ref}"
                            )
                    selected_claims[side] = claim_refs

                overlap = set(selected_claims["supporting"]) & set(
                    selected_claims["contradicting"]
                )
                if overlap:
                    raise Stage2MaturityAsOfMaterializationError(
                        f"stage2_materialization_atomic_claim_overlap:"
                        f"{ticker}:{row_index}:{','.join(sorted(overlap))}"
                    )

                for side in ("supporting", "contradicting"):
                    projected: list[str] = []
                    for claim_ref in selected_claims[side]:
                        for source_ref in catalog_by_ref[claim_ref].parent_source_refs:
                            if source_ref not in projected:
                                projected.append(source_ref)
                    row[f"{side}_evidence_refs"] = projected
                    cited_refs.extend(projected)
            else:
                for field_name in (
                    "supporting_evidence_refs",
                    "contradicting_evidence_refs",
                ):
                    values = row.get(field_name)
                    if not isinstance(values, list) or any(
                        not isinstance(value, str) for value in values
                    ):
                        raise Stage2MaturityAsOfMaterializationError(
                            f"stage2_materialization_ref_list_invalid:"
                            f"{ticker}:{row_index}:{field_name}"
                        )
                    cited_refs.extend(values)
            if normalized_contract == STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT:
                concrete_dates = []
                for ref_id in cited_refs:
                    evidence_row = evidence.get(ref_id)
                    if evidence_row is None:
                        raise Stage2MaturityAsOfMaterializationError(
                            f"stage2_materialization_unknown_ticker_local_ref:"
                            f"{ticker}:{row_index}:{ref_id}"
                        )
                    resolved = concrete_evidence_date(evidence_row.as_of)
                    if resolved is not None:
                        concrete_dates.append(resolved)
                if not concrete_dates:
                    raise Stage2MaturityAsOfMaterializationError(
                        f"stage2_materialization_no_concrete_owned_date:"
                        f"{ticker}:{row_index}"
                    )
                derived = max(concrete_dates)
                if derived > assessment_date:
                    raise Stage2MaturityAsOfMaterializationError(
                        f"stage2_materialization_future_derived_date:"
                        f"{ticker}:{row_index}:{derived.isoformat()}"
                    )
                row["as_of"] = derived.isoformat()
                continue

            projection = project_maturity_provenance(evidence, cited_refs)
            if projection.invalid_ref_ids:
                raise Stage2MaturityAsOfMaterializationError(
                    f"stage2_materialization_unresolvable_provenance:"
                    f"{ticker}:{row_index}:{','.join(projection.invalid_ref_ids)}"
                )
            if projection.provenance_status is None:
                raise Stage2MaturityAsOfMaterializationError(
                    f"stage2_materialization_no_valid_provenance:"
                    f"{ticker}:{row_index}"
                )
            derived = concrete_evidence_date(projection.as_of)
            if derived is not None and derived > assessment_date:
                raise Stage2MaturityAsOfMaterializationError(
                    f"stage2_materialization_future_derived_date:"
                    f"{ticker}:{row_index}:{derived.isoformat()}"
                )
            row["as_of"] = projection.as_of
            row["provenance_status"] = projection.provenance_status.value

    if normalized_contract == STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT:
        payload["contract"] = OUTPUT_CONTRACT
        return AcceptedV2ProductionBatchOutput.model_validate(payload)
    payload["contract"] = OUTPUT_CONTRACT_V2
    return AcceptedV2ProductionBatchOutputV2.model_validate(payload)


def accepted_v2_fundamental_core_prompt(
    context: AcceptedV2ProductionContext,
    *,
    subjects: Sequence[str] | None = None,
) -> str:
    selected = tuple(subjects or context.selected_subjects)
    packets = {row.ticker: row for row in context.evidence_packets}
    ownership = {row.ticker: row for row in context.evidence_ownership}
    if not selected or not set(selected).issubset(packets):
        raise ValueError("v2_fundamental_core_prompt_subject_mismatch")
    ref_catalog = accepted_v2_fundamental_core_ref_catalog_manifest(
        context,
        subjects=selected,
    )
    identity = {
        "contract": FUNDAMENTAL_CORE_CONTRACT,
        "packet_id": context.packet_id,
        "claim_id": context.claim_id,
        "market": context.market,
        "assessment_date": context.assessment_date,
    }
    ref_catalog_identity = {
        "contract": ref_catalog["contract"],
        "ref_catalog_hash": ref_catalog["ref_catalog_hash"],
        "ref_catalog_count": ref_catalog["ref_catalog_count"],
    }
    payload = [
        {
            "fundamental_core_evidence": _compact_owned_evidence(
                packets[ticker], ownership[ticker].core_ref_ids
            ),
            "expectation_valuation_interaction": ownership[
                ticker
            ].expectation_valuation.model_dump(mode="json"),
        }
        for ticker in selected
    ]
    return (
        """You own the immutable fundamental/economic core of a three-axis monitored decision. Use only FUNDAMENTAL_CORE_EVIDENCE. You cannot see or use price, support/resistance, confirmation-price status, OHLCV technicals, short-term flow/positioning, or futures. Do not browse, use later facts, calculate unregistered numbers, target prices, stops, order sizes, or fixed scores.

Emit exactly one core for every supplied ticker as an AcceptedV2FundamentalCoreCandidate, in the same order as FUNDAMENTAL_CORE_CONTEXT. Do not omit, duplicate, replace, or reorder subjects. Decide overall BUY/HOLD/SELL, directional balance, confidence, core buy/sell drivers, decisive reason, and the existing-holder fundamental stance. Holder HOLDABLE/REVIEW/REDUCE must be based only on fundamental holding risk. REVIEW means the holding thesis needs re-examination; it is not an automatic sell instruction. REDUCE requires sufficiently severe or persistent fundamental downside. Do not derive holder stance mechanically from overall direction or Business Delta.

The pair directional_balance must sum to 10 and use integer or 0.5 increments. Derive the label exactly: BUY when buy >= 6, SELL when sell >= 6, HOLD otherwise. The balance is relative directional force, not probability or a weighted score. Every claim must be concise natural Korean and cite exact supplied refs. Evidence refs are identifiers. Copy them exactly from the supplied evidence catalog. Never synthesize, shorten, edit, guess, or repair an evidence ref. If no valid ref supports a claim, do not cite one.

Use EXPECTATION_VALUATION_INTERACTION as an evidence-ownership rule. INDEPENDENT inputs may remain separate concepts. PARTIALLY_OVERLAPPING inputs must not count shared lineage twice. VALUATION_DERIVED_EXPECTATION_ONLY and UNKNOWN expectation evidence may remain context but cannot become an independent directional driver. Do not force any ticker or create a pro-BUY bias.

Return strict JSON only. Copy every FUNDAMENTAL_CORE_IDENTITY field exactly and include no core outside the supplied ticker set.

FUNDAMENTAL_CORE_IDENTITY:
"""
        + json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
        + """

FUNDAMENTAL_CORE_REF_CATALOG_IDENTITY:
"""
        + json.dumps(ref_catalog_identity, ensure_ascii=False, separators=(",", ":"))
        + """

FUNDAMENTAL_CORE_CONTEXT:
"""
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def accepted_v2_production_prompt(
    context: AcceptedV2ProductionContext,
    *,
    fundamental_cores: Sequence[AcceptedV2FundamentalCoreCandidate],
    subjects: Sequence[str] | None = None,
) -> str:
    selected = tuple(subjects or context.selected_subjects)
    packets = {row.ticker: row for row in context.evidence_packets}
    ownership = {row.ticker: row for row in context.evidence_ownership}
    prior = {row.ticker: row for row in context.prior_accepted}
    cores = {row.ticker: row for row in fundamental_cores}
    if not selected or not set(selected).issubset(packets) or not set(selected).issubset(cores):
        raise ValueError("v2_production_prompt_subject_mismatch")
    identity = {
        "contract": STAGE2_MODEL_OUTPUT_CONTRACT,
        "packet_id": context.packet_id,
        "claim_id": context.claim_id,
        "market": context.market,
        "assessment_date": context.assessment_date,
    }
    selected_cores = tuple(cores[ticker] for ticker in selected)
    ref_catalog = accepted_v2_stage2_ref_catalog_manifest(
        context,
        subjects=selected,
        fundamental_cores=selected_cores,
    )
    ref_catalog_identity = {
        "contract": ref_catalog["contract"],
        "shared_contract": ref_catalog["shared_contract"],
        "ref_catalog_hash": ref_catalog["ref_catalog_hash"],
        "ref_catalog_count": ref_catalog["ref_catalog_count"],
        "maturity_date_catalog_hash": ref_catalog["maturity_date_catalog_hash"],
        "maturity_date_count": ref_catalog["maturity_date_count"],
        "maturity_polarity_adapter_contract": ref_catalog[
            "maturity_polarity_adapter_contract"
        ],
        "maturity_atomic_identity_contract": ref_catalog[
            "maturity_atomic_identity_contract"
        ],
        "maturity_atomic_claim_catalog_hash": ref_catalog[
            "maturity_atomic_claim_catalog_hash"
        ],
        "maturity_atomic_claim_count": ref_catalog["maturity_atomic_claim_count"],
    }
    atomic_claims_by_ticker: dict[str, list[dict[str, object]]] = {}
    for row in ref_catalog["maturity_atomic_claims"]:
        if isinstance(row, dict):
            atomic_claims_by_ticker.setdefault(str(row.get("ticker") or ""), []).append(row)
    payload = [
        {
            "frozen_fundamental_core": cores[ticker].model_dump(mode="json"),
            "fundamental_core_sha256": accepted_v2_fundamental_core_sha256(cores[ticker]),
            "fundamental_core_evidence": _compact_stage2_owned_evidence(
                packets[ticker], ownership[ticker].core_ref_ids
            ),
            "price_timing_evidence": _compact_stage2_owned_evidence(
                packets[ticker], ownership[ticker].timing_ref_ids
            ),
            "expectation_valuation_interaction": ownership[
                ticker
            ].expectation_valuation.model_dump(mode="json"),
            "maturity_atomic_claim_catalog": atomic_claims_by_ticker.get(ticker, []),
            "prior_accepted": (prior[ticker].model_dump(mode="json") if ticker in prior else None),
        }
        for ticker in selected
    ]
    return (
        """You complete a production-bound V2 three-axis analytical candidate around a FROZEN_FUNDAMENTAL_CORE and perform any required accepted-decision adjudication. Use only supplied canonical evidence. Do not browse, use later facts, calculate unregistered numbers, target prices, stops, order sizes, or fixed scores.

Copy every frozen core field exactly into the complete candidate: ticker, decision, directional_balance, buy_drivers, sell_drivers, balance_summary, confidence, decisive_reason, and holder_axis. Copy fundamental_core_sha256 exactly. Price/timing evidence must never mutate these fields. Use price/timing, valuation, expectations, confirmation need, and uncertainty only to form timing and the independent new_buyer_axis. Overall BUY can coexist with new-buyer WAIT, overall SELL can coexist with holder HOLDABLE, and overall HOLD does not force WAIT. Do not mechanically map any axis from another.

Holder REVIEW means 보유 근거 재검토, not an automatic sell. Holder REDUCE must remain fundamental and may not cite price, technical, flow, confirmation-price, or futures evidence. A configured price confirmation is an entry/price check, never a fundamental business confirmation. Futures, when present in a timing-only context, cannot create Business Delta, holder risk, or a fundamental direction change.

"""
        + PRECONFIRMATION_BUY_STAGE2_PROMPT_RULE
        + """

Set post_confirmation_hold=true only when decision=HOLD and overall_maturity.maturity=CONFIRMED. If overall_maturity.maturity is not CONFIRMED, set post_confirmation_hold=false and postconfirmation_hold_explanation=null. A HOLD decision alone does not imply post_confirmation_hold=true; do not change the decision or maturity merely to satisfy this flag.

Use EXPECTATION_VALUATION_INTERACTION as an evidence-ownership rule. Never count the same underlying valuation signal once as high expectations and again as expensive valuation. Preserve genuinely independent expectation evidence. Do not force GOOGL or any other ticker to a target enum.

For every supplied ticker, emit exactly one PreconfirmationDecisionCandidate in candidates. Use VERY_HIGH reasoning_grade and concise natural Korean for every prose claim. Evidence refs are exact opaque identifiers. Copy only refs present in the supplied Stage-2 evidence catalog. Never edit, append, shorten, infer, synthesize, guess, or repair an evidence ref. If no exact supplied ref supports a statement, do not cite one. Distinguish factual safety from investment uncertainty. Evaluate evidence maturity, expectations, pricing requirement, Bear/Base/Bull scenarios, asymmetry, confirmation cost, and preconfirmation error cost without a weighted score. BUY before full confirmation is allowed only when the structured contract permits it. Confirmed business evidence can still be HOLD or SELL when expectations are demanding. Technical and market evidence may own timing, not long-horizon business asymmetry.

The runtime owns driver_maturity source-evidence refs and row-level provenance materialization. Do not emit supporting_evidence_refs, contradicting_evidence_refs, as_of, or provenance_status. Do not emit or infer driver_maturity.as_of. Source evidence refs are projected from the selected atomic claims; source-ref selection and provenance scalar derivation are not model tasks.

For every driver_maturity row, supporting_claim_refs must contain at least one exact same-ticker claim_ref from that ticker's MATURITY_ATOMIC_CLAIM_CATALOG. If no supplied atomic claim supports a proposed driver, do not emit that driver; choose a driver that is actually represented by the supplied atomic claims. contradicting_claim_refs may be empty when no canonical atomic claim contradicts the driver. These claim refs identify already-structured frozen-core propositions; never create, alter, approximate, shorten, infer, split, or repair one. Source evidence refs are runtime-owned and cannot substitute for a missing atomic claim identity. The two atomic claim sets must be disjoint. The runtime projects each side's exact parent source refs from these selected claims. One mixed parent source may appear on both projected source-ref sides only when different canonical atomic claims from that parent are used on the two sides. Absolute BULLISH/BEARISH polarity is metadata about the proposition, while supporting/contradicting is relative to the specific maturity driver; do not equate them.

Emit directional_balance, buy_drivers, sell_drivers, and balance_summary from the current evidence. The pair must sum to 10 and use integer or 0.5 increments. Derive the label exactly: BUY when buy >= 6, SELL when sell >= 6, HOLD otherwise. HOLD is current neutrality and must not inherit the prior label. The balance is relative directional force, not probability, expected return, odds, or a fixed-factor weighted score. Every buy/sell driver must cite exact canonical evidence refs.

Read technical_context_status and technical_context_quality explicitly. PARTIAL_SAFE or UNAVAILABLE is a documented evidence limit, never a neutral technical signal and never an automatic HOLD. When the missing technical evidence materially prevents entry-timing assessment, use timing=INSUFFICIENT and cite the technical-context quality ref; otherwise explain which packet-owned price or non-technical evidence safely supports timing. Never invent a missing timeframe.

The prior accepted decision and balance are continuity evidence, not a target distribution. Fresh evidence may justify a different candidate. Emit one AcceptedV2Adjudication when the candidate label differs from prior accepted, or when unchanged evidence produces an absolute BUY-balance move of at least 1.5. Do not adjudicate trivial ratio movement. In this legacy-compatible adjudication schema, v1_decision means prior accepted decision and v2_decision means the new candidate. KEEP_V1 preserves the prior accepted label, balance, and directional drivers when those prior fields are available; KEEP_V2 accepts the new candidate label, balance, and directional drivers exactly. Every adjudication must emit its accepted balance and accepted directional drivers. NEEDS_REPAIR is allowed when no final accepted result is safe. Explain the decisive basis with canonical refs. If evidence is unchanged, do not change the accepted top-level decision or make a materially unexplained accepted balance jump.

Change conditions are reassessment conditions, not automatic trades. Never describe a self transition: BUY must not be raised to BUY, HOLD must not be lowered to HOLD, and SELL must not be lowered to SELL. Refer to confidence/timing/risk when staying inside the same top-level decision.

Canonical evidence may include logical_condition metadata. When an upgrade_condition or downgrade_condition cites a composite logical condition, emit EvidenceClaim.logical_condition. Copy the source object's explicit source_condition_ref, severity, operator, and condition IDs exactly. Do not use the enclosing evidence ref as source_condition_ref. In claim expressions, LEAF requires leaf_ref and forbids children; ANY_OF/ALL_OF require children and forbid leaf_ref. For a LEAF-only source, leave claim logical_condition null. Use coverage_mode=FULL only when the full source tree is represented without changing ANY_OF to ALL_OF or ALL_OF to ANY_OF and without deleting a branch. A one-branch illustration must use NON_EXHAUSTIVE_EXAMPLE. Do not infer or reconstruct condition IDs.

Do not introduce or infer ROIC, CCC, DSO, DPO, runway months, FCF yield, per-share FCF, EV/FCF, or P/FCF in Stage-2-owned fields. Frozen FUNDAMENTAL_CORE fields must still be copied exactly, including any already-validated prospective thesis conditions they contain. Do not modify frozen core text merely to satisfy Stage-2 metric restrictions. Never abbreviate, truncate, or reconstruct an evidence ref ID; copy every cited ref exactly from the supplied context.

Do not emit internal phrases such as 상향 라벨, 하향 라벨, or 내부 위험 확신. Every sentence must end as a complete user-facing Korean sentence.

Return strict JSON only. Set fundamental_cores to the supplied frozen cores exactly. Copy every PRODUCTION_V2_IDENTITY field exactly and include no candidate or adjudication outside the supplied ticker set.

PRODUCTION_V2_IDENTITY:
"""
        + json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
        + """

STAGE2_REF_CATALOG_IDENTITY:
"""
        + json.dumps(ref_catalog_identity, ensure_ascii=False, separators=(",", ":"))
        + """

PRODUCTION_V2_CONTEXT:
"""
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def accepted_v2_production_repair_prompt(
    context: AcceptedV2ProductionContext,
    *,
    fundamental_core: AcceptedV2FundamentalCoreCandidate,
    ticker: str,
    rejected_candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
    validation_errors: Sequence[str],
) -> str:
    if ticker != rejected_candidate.ticker:
        raise ValueError("v2_production_repair_ticker_mismatch")
    repair_hints: list[str] = []
    if any(error.startswith("future_maturity_evidence:") for error in validation_errors):
        repair_hints.append(
            "For every future_maturity_evidence driver, select only exact same-row evidence "
            "refs whose canonical concrete dates are not later than assessment_date. The "
            "runtime derives driver_maturity.as_of; do not emit or infer it."
        )
    if "postconfirmation_hold_without_confirmed_maturity" in validation_errors:
        repair_hints.append(
            "A HOLD candidate with overall_maturity other than CONFIRMED must set "
            "post_confirmation_hold=false and postconfirmation_hold_explanation=null. Preserve "
            "the HOLD decision unless canonical evidence independently requires a change."
        )
    return (
        accepted_v2_production_prompt(
            context,
            fundamental_cores=(fundamental_core,),
            subjects=(ticker,),
        )
        + "\n\nBOUNDED_VALIDATOR_REPAIR:\n"
        + json.dumps(
            {
                "ticker": ticker,
                "validation_errors": list(validation_errors),
                "rejected_candidate": _stage2_model_facing_candidate_payload(
                    rejected_candidate
                ),
                "instructions": (
                    "Repair only the listed contract violations. Preserve the analytical "
                    "decision unless the supplied canonical evidence requires otherwise. "
                    "Return exactly one complete candidate and any adjudication required by "
                    "the prior accepted decision. Use only exact supplied evidence ref IDs."
                ),
                "error_specific_repair_hints": repair_hints,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
    )


def accepted_v2_production_batch_schema_repair_prompt(
    context: AcceptedV2ProductionContext,
    *,
    fundamental_cores: Sequence[AcceptedV2FundamentalCoreCandidate],
    subjects: Sequence[str],
    rejected_output: Mapping[str, object],
    validation_errors: Sequence[str],
) -> str:
    selected = tuple(str(ticker).upper() for ticker in subjects)
    if not selected or any(ticker not in context.selected_subjects for ticker in selected):
        raise ValueError("v2_production_batch_repair_subject_mismatch")
    return (
        accepted_v2_production_prompt(
            context,
            fundamental_cores=fundamental_cores,
            subjects=selected,
        )
        + "\n\nBOUNDED_BATCH_SCHEMA_REPAIR:\n"
        + json.dumps(
            {
                "subjects": list(selected),
                "validation_errors": list(validation_errors),
                "rejected_output": _stage2_model_facing_rejected_output(
                    rejected_output
                ),
                "instructions": (
                    "Repair only the listed schema or cross-field contract violations. "
                    "Return the complete batch for exactly the supplied subjects. Preserve each "
                    "analytical decision unless correcting the violation requires a change, and "
                    "use only exact supplied evidence ref IDs."
                ),
            },
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
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
    repeated = [(text, count) for text, count in Counter(substantive).items() if count >= 2]
    repetition_assessments = [
        {
            "span": text,
            "stock_count": count,
            "classification": classify_repeated_span(
                text,
                stock_count=count,
                evidence_signature_count=count,
            ),
        }
        for text, count in repeated
    ]
    if any(
        item["classification"] == RepetitionClass.MATERIAL_SPAM_REPEAT
        for item in repetition_assessments
    ):
        errors.append("cross_ticker_material_spam_repetition")
    return {
        "contract": "v2-accepted-production-message-quality-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
        "message_count": len(rendered),
        "repeated_substantive_span_count": len(repeated),
        "repetition_assessments": repetition_assessments,
        "soft_quality_warning_count": sum(
            item["classification"] != RepetitionClass.MATERIAL_SPAM_REPEAT
            for item in repetition_assessments
        ),
        "numeric_claim_count": 0,
        "manual_numeric_count": 0,
        "unresolved_numeric_count": 0,
    }


def validate_accepted_v2_production_output(
    context: AcceptedV2ProductionContext,
    output: AcceptedV2ProductionBatchOutput | AcceptedV2ProductionBatchOutputV2,
    *,
    trusted_fundamental_core_batch: AcceptedV2FundamentalCoreBatch | None = None,
    validated_at: datetime | None = None,
) -> AcceptedV2ProductionArtifact | AcceptedV2ProductionArtifactV2:
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
    ownership = {row.ticker: row for row in context.evidence_ownership}
    cores = {row.ticker: row for row in output.fundamental_cores}
    candidates = {row.ticker: row for row in output.candidates}
    if set(ownership) != set(context.selected_subjects) or len(ownership) != len(
        context.evidence_ownership
    ):
        raise ValueError("v2_production_ownership_scope_mismatch")
    if set(cores) != set(context.selected_subjects) or len(cores) != len(
        output.fundamental_cores
    ):
        raise ValueError("v2_production_fundamental_core_scope_mismatch")
    if set(candidates) != set(context.selected_subjects) or len(candidates) != len(
        output.candidates
    ):
        raise ValueError("v2_production_candidate_scope_mismatch")
    trusted_cores: dict[str, AcceptedV2FundamentalCoreCandidate] = {}
    if trusted_fundamental_core_batch is not None:
        trusted_scope_errors = validate_accepted_v2_fundamental_core_batch_scope(
            trusted_fundamental_core_batch,
            context,
            subjects=context.selected_subjects,
        )
        if trusted_scope_errors:
            raise ValueError(
                "v2_production_trusted_fundamental_core_scope_mismatch:"
                + ",".join(trusted_scope_errors)
            )
        trusted_cores = {
            row.ticker: row for row in trusted_fundamental_core_batch.cores
        }
        for ticker in context.selected_subjects:
            if cores[ticker] != trusted_cores[ticker]:
                raise ValueError(
                    f"v2_production_trusted_fundamental_core_mismatch:{ticker}"
                )
    for ticker, candidate in candidates.items():
        ownership_errors = validate_accepted_v2_candidate_ownership(
            candidate,
            cores[ticker],
            ownership[ticker],
        )
        if ownership_errors:
            raise ValueError(
                "v2_production_candidate_ownership_invalid:"
                + ticker
                + ":"
                + ",".join(ownership_errors)
            )
        validation = validate_accepted_v2_stage2_candidate(
            packets[ticker],
            candidate,
            cores[ticker],
            ownership[ticker],
        )
        if not validation.valid:
            raise ValueError(
                "v2_production_candidate_invalid:" + ticker + ":" + ",".join(validation.errors)
            )
    prior = {row.ticker: row for row in context.prior_accepted}
    adjudications = {row.ticker: row for row in output.adjudications}
    if len(adjudications) != len(output.adjudications):
        raise ValueError("v2_production_duplicate_adjudication")
    adjudication_required = {
        ticker
        for ticker, candidate in candidates.items()
        if ticker in prior
        and requires_directional_balance_adjudication(
            prior_decision=prior[ticker].accepted_decision,
            prior_balance=prior[ticker].accepted_directional_balance,
            prior_evidence_sha256=prior[ticker].evidence_sha256,
            candidate_decision=candidate.decision,
            candidate_balance=candidate.directional_balance,
            current_evidence_sha256=packets[ticker].evidence_sha256,
        )
    }
    if set(adjudications) - adjudication_required:
        raise ValueError("v2_production_unrequired_adjudication")
    plans: list[AcceptedDecisionPlan] = []
    rendered: list[RenderedProductionAcceptedDecision] = []
    blocks: list[AcceptedV2ProductionBlock] = []
    for ticker in context.selected_subjects:
        packet = packets[ticker]
        candidate = candidates[ticker]
        baseline = prior.get(ticker)
        material_disagreement = ticker in adjudication_required
        plan = resolve_accepted_v2_decision(
            packet,
            candidate,
            v1_decision=(baseline.accepted_decision if baseline else candidate.decision),
            v1_directional_balance=(baseline.accepted_directional_balance if baseline else None),
            v1_buy_drivers=(baseline.accepted_buy_drivers if baseline else ()),
            v1_sell_drivers=(baseline.accepted_sell_drivers if baseline else ()),
            v1_balance_summary=(baseline.accepted_balance_summary if baseline else None),
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
        trusted_core = trusted_cores.get(ticker)
        frozen_core_numeric_scope = (
            AcceptedDecisionFrozenCoreNumericScope(
                ticker=ticker,
                fundamental_core_sha256=accepted_v2_fundamental_core_sha256(
                    trusted_core
                ),
                directional_balance=trusted_core.directional_balance,
                buy_drivers=trusted_core.buy_drivers,
                sell_drivers=trusted_core.sell_drivers,
                balance_summary=trusted_core.balance_summary,
            )
            if trusted_core is not None
            else None
        )
        validation = validate_accepted_v2_decision(
            packet,
            plan,
            frozen_core_numeric_scope=frozen_core_numeric_scope,
        )
        if not validation.valid:
            raise ValueError(
                "v2_production_accepted_plan_invalid:" + ticker + ":" + ",".join(validation.errors)
            )
        rendered_row = render_accepted_v2_production(
            packet,
            plan,
            frozen_core_numeric_scope=frozen_core_numeric_scope,
        )
        rendered.append(rendered_row)
        assert plan.accepted_decision is not None
        assert plan.accepted_decision_id is not None
        blocks.append(
            AcceptedV2ProductionBlock(
                ticker=ticker,
                decision=plan.accepted_decision,
                accepted_decision_id=plan.accepted_decision_id,
                buy_balance=(
                    plan.accepted_directional_balance.buy
                    if plan.accepted_directional_balance is not None
                    else None
                ),
                sell_balance=(
                    plan.accepted_directional_balance.sell
                    if plan.accepted_directional_balance is not None
                    else None
                ),
                new_buyer_stance=(
                    plan.accepted_new_buyer_axis.stance
                    if plan.accepted_new_buyer_axis is not None
                    else None
                ),
                holder_stance=(
                    plan.accepted_holder_axis.stance
                    if plan.accepted_holder_axis is not None
                    else None
                ),
                text=rendered_row.text,
            )
        )
    quality = _production_message_quality(rendered)
    if quality["status"] != "PASS":
        raise ValueError("v2_production_message_quality_failed")
    from app.services.accepted_decision_consistency_service import (
        audit_accepted_decision_consistency,
    )

    consistency = audit_accepted_decision_consistency(
        evidence_packets=context.evidence_packets,
        prior_accepted=context.prior_accepted,
        accepted_plans=tuple(plans),
        blocks=tuple(blocks),
    )
    if consistency.status != "PASS":
        changed_without_evidence = next(
            (
                row.ticker
                for row in consistency.diagnostics
                if "same_evidence_accepted_decision_drift" in row.errors
            ),
            None,
        )
        if changed_without_evidence is not None:
            raise ValueError(
                "v2_production_same_evidence_unexplained_churn:" + changed_without_evidence
            )
        balance_drift_without_evidence = next(
            (
                row.ticker
                for row in consistency.diagnostics
                if "same_evidence_accepted_balance_drift" in row.errors
            ),
            None,
        )
        if balance_drift_without_evidence is not None:
            raise ValueError(
                "v2_production_same_evidence_unexplained_balance_drift:"
                + balance_drift_without_evidence
            )
        raise ValueError("v2_production_unexplained_accepted_decision_drift")
    ready_count = len(blocks)
    not_ready_count = len(context.selected_subjects) - ready_count
    artifact_type = (
        AcceptedV2ProductionArtifactV2
        if isinstance(output, AcceptedV2ProductionBatchOutputV2)
        else AcceptedV2ProductionArtifact
    )
    return artifact_type(
        status="PASS" if not_ready_count == 0 else "PARTIAL_SAFE",
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        source_packet_sha256=context.source_packet_sha256,
        selected_subjects=context.selected_subjects,
        evidence_packets=context.evidence_packets,
        evidence_ownership=context.evidence_ownership,
        fundamental_cores=tuple(cores[ticker] for ticker in context.selected_subjects),
        candidates=tuple(candidates[ticker] for ticker in context.selected_subjects),
        accepted_plans=tuple(plans),
        blocks=tuple(blocks),
        ready_count=ready_count,
        not_ready_count=not_ready_count,
        message_quality=quality,
        decision_consistency=consistency.model_dump(mode="json"),
        validated_at=(validated_at or datetime.now(UTC)).astimezone(UTC).isoformat(),
    )


def load_accepted_v2_production_artifact(
    path: Path,
    *,
    packet: Mapping[str, object],
    claim_id: str,
    trusted_fundamental_core_batch: AcceptedV2FundamentalCoreBatch | None = None,
) -> AcceptedV2ProductionArtifact | AcceptedV2ProductionArtifactV2:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("v2_production_artifact_payload_invalid")
    artifact = parse_accepted_v2_production_artifact(payload)
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
    ownership = {row.ticker: row for row in artifact.evidence_ownership}
    cores = {row.ticker: row for row in artifact.fundamental_cores}
    candidates = {row.ticker: row for row in artifact.candidates}
    plans = {row.ticker: row for row in artifact.accepted_plans}
    blocks = {row.ticker: row for row in artifact.blocks}
    if any(
        set(rows) != set(subjects)
        for rows in (packets, ownership, cores, candidates, plans)
    ):
        raise ValueError("v2_production_artifact_subject_mismatch")
    trusted_cores: dict[str, AcceptedV2FundamentalCoreCandidate] = {}
    if trusted_fundamental_core_batch is not None:
        trusted_context = AcceptedV2ProductionContext(
            packet_id=artifact.packet_id,
            claim_id=artifact.claim_id,
            market=artifact.market,
            assessment_date=artifact.assessment_date,
            source_packet_sha256=artifact.source_packet_sha256,
            selected_subjects=artifact.selected_subjects,
            evidence_packets=artifact.evidence_packets,
            evidence_ownership=artifact.evidence_ownership,
            prepared_at=artifact.validated_at,
        )
        trusted_scope_errors = validate_accepted_v2_fundamental_core_batch_scope(
            trusted_fundamental_core_batch,
            trusted_context,
            subjects=artifact.selected_subjects,
        )
        if trusted_scope_errors:
            raise ValueError(
                "v2_production_artifact_trusted_fundamental_core_scope_mismatch:"
                + ",".join(trusted_scope_errors)
            )
        trusted_cores = {
            row.ticker: row for row in trusted_fundamental_core_batch.cores
        }
        for ticker in artifact.selected_subjects:
            if cores[ticker] != trusted_cores[ticker]:
                raise ValueError(
                    f"v2_production_artifact_trusted_fundamental_core_mismatch:{ticker}"
                )
    for ticker, plan in plans.items():
        validation_core = trusted_cores.get(ticker, cores[ticker])
        candidate_validation = validate_accepted_v2_stage2_candidate(
            packets[ticker],
            candidates[ticker],
            validation_core,
            ownership[ticker],
        )
        if not candidate_validation.valid:
            raise ValueError(
                "v2_production_artifact_candidate_invalid:"
                + ticker
                + ":"
                + ",".join(candidate_validation.errors)
            )
        if plan.status != AcceptedDecisionStatus.READY:
            if ticker in blocks:
                raise ValueError("v2_production_not_ready_block_visible")
            continue
        trusted_core = trusted_cores.get(ticker)
        frozen_core_numeric_scope = (
            AcceptedDecisionFrozenCoreNumericScope(
                ticker=ticker,
                fundamental_core_sha256=accepted_v2_fundamental_core_sha256(
                    trusted_core
                ),
                directional_balance=trusted_core.directional_balance,
                buy_drivers=trusted_core.buy_drivers,
                sell_drivers=trusted_core.sell_drivers,
                balance_summary=trusted_core.balance_summary,
            )
            if trusted_core is not None
            else None
        )
        expected = render_accepted_v2_production(
            packets[ticker],
            plan,
            frozen_core_numeric_scope=frozen_core_numeric_scope,
        )
        block = blocks.get(ticker)
        if (
            block is None
            or block.decision != plan.accepted_decision
            or block.accepted_decision_id != plan.accepted_decision_id
            or plan.accepted_directional_balance is None
            or block.buy_balance != plan.accepted_directional_balance.buy
            or block.sell_balance != plan.accepted_directional_balance.sell
            or plan.accepted_new_buyer_axis is None
            or block.new_buyer_stance != plan.accepted_new_buyer_axis.stance
            or plan.accepted_holder_axis is None
            or block.holder_stance != plan.accepted_holder_axis.stance
            or block.text != expected.text
        ):
            raise ValueError("v2_production_artifact_block_mismatch")
    return artifact


def advance_accepted_v2_state(
    artifact: AcceptedV2ProductionArtifact | AcceptedV2ProductionArtifactV2,
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
        AcceptedV2ProductionState(entries=tuple(entries[ticker] for ticker in sorted(entries))),
        settings=settings,
    )


def accepted_v2_runtime_preconditions(*, settings: Settings | None = None) -> dict[str, object]:
    current = settings or get_settings()
    checks = {
        "visible_engine_v2_accepted": current.visible_stock_decision_engine == "v2_accepted",
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
