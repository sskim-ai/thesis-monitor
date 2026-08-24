from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from urllib.parse import urlparse

from app.services.ai_analyst_vnext_shadow_service import numeric_tokens


CONTRACT_VERSION = "open-research-event-attribution-shadow-v1"


class SourceTier(StrEnum):
    TIER_1_PRIMARY = "TIER_1_PRIMARY"
    TIER_2_INDEPENDENT = "TIER_2_INDEPENDENT"
    TIER_3_SECONDARY = "TIER_3_SECONDARY"
    TIER_4_LEAD_ONLY = "TIER_4_LEAD_ONLY"


class SourceType(StrEnum):
    ISSUER_OFFICIAL = "ISSUER_OFFICIAL"
    EXCHANGE_REGULATOR = "EXCHANGE_REGULATOR"
    GOVERNMENT_OFFICIAL = "GOVERNMENT_OFFICIAL"
    WIRE_NEWS = "WIRE_NEWS"
    BUSINESS_PRESS = "BUSINESS_PRESS"
    SECONDARY_REPORT = "SECONDARY_REPORT"
    COMMUNITY_LEAD = "COMMUNITY_LEAD"


class RelationshipType(StrEnum):
    DIRECT_ISSUER = "DIRECT_ISSUER"
    CUSTOMER = "CUSTOMER"
    SUPPLIER = "SUPPLIER"
    PEER = "PEER"
    SECTOR = "SECTOR"
    MACRO = "MACRO"
    MARKET_STRUCTURE = "MARKET_STRUCTURE"


class EvidenceType(StrEnum):
    CONFIRMED_EVENT_FACT = "CONFIRMED_EVENT_FACT"
    CONFIRMED_MARKET_FACT = "CONFIRMED_MARKET_FACT"
    CONFIRMED_FLOW_FACT = "CONFIRMED_FLOW_FACT"
    CONFIRMED_BREADTH_FACT = "CONFIRMED_BREADTH_FACT"
    REPORTED_INTERPRETATION = "REPORTED_INTERPRETATION"
    NEGATIVE_EVIDENCE = "NEGATIVE_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class CurrentnessRole(StrEnum):
    CURRENT_SESSION = "CURRENT_SESSION"
    PRE_SESSION_EVENT = "PRE_SESSION_EVENT"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    UPCOMING_EVENT = "UPCOMING_EVENT"
    AFTER_MOVE_INTERPRETATION = "AFTER_MOVE_INTERPRETATION"


class EventClusterType(StrEnum):
    COMPANY_SPECIFIC_CATALYST = "COMPANY_SPECIFIC_CATALYST"
    SECTOR_INDUSTRY_CATALYST = "SECTOR_INDUSTRY_CATALYST"
    MARKET_BREADTH_ROTATION = "MARKET_BREADTH_ROTATION"
    POSITIONING_FLOW = "POSITIONING_FLOW"
    MACRO_RATES_FX = "MACRO_RATES_FX"
    TECHNICAL_MECHANICAL = "TECHNICAL_MECHANICAL"
    UPCOMING_EVENT_RISK = "UPCOMING_EVENT_RISK"
    UNKNOWN = "UNKNOWN"


class HypothesisScope(StrEnum):
    COMPANY = "company"
    SECTOR = "sector"
    MARKET = "market"
    MACRO = "macro"
    POSITIONING = "positioning"


class AttributionStrength(StrEnum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    UNRESOLVED = "UNRESOLVED"


class ResearchSupportType(StrEnum):
    RESEARCH_DIRECT_FACT = "RESEARCH_DIRECT_FACT"
    RESEARCH_REPORTED_INTERPRETATION = "RESEARCH_REPORTED_INTERPRETATION"
    EVENT_ATTRIBUTION_INFERENCE = "EVENT_ATTRIBUTION_INFERENCE"
    NEGATIVE_EVIDENCE_BOUNDARY = "NEGATIVE_EVIDENCE_BOUNDARY"
    CROSS_SECTIONAL_SYNTHESIS = "CROSS_SECTIONAL_SYNTHESIS"
    MARKET_BREADTH_SYNTHESIS = "MARKET_BREADTH_SYNTHESIS"
    UPCOMING_EVENT_CHECK = "UPCOMING_EVENT_CHECK"


class ResearchRenderer(StrEnum):
    DIRECT_ANALYST = "DIRECT_ANALYST"
    CONCISE_HYBRID = "CONCISE_HYBRID"
    EXISTING_NO_RESEARCH = "EXISTING_NO_RESEARCH"


@dataclass(frozen=True)
class ResearchSource:
    source_id: str
    name: str
    tier: SourceTier
    source_type: SourceType
    source_ref: str
    source_family: str
    original_source: str
    syndicated_from: str | None = None
    independent_confirmation: bool = True


@dataclass(frozen=True)
class SearchLogEntry:
    research_cluster_id: str
    query: str
    created_at: str
    reason: str
    parent_query: str | None
    result_count: int
    selected_sources: tuple[str, ...]
    rejected_sources: tuple[str, ...]


@dataclass(frozen=True)
class NegativeEvidenceScope:
    question: str
    searched_source_tiers: tuple[SourceTier, ...]
    query_count: int
    searched_time_window: str
    entities_or_sectors_checked: tuple[str, ...]
    last_search_at: str
    what_was_not_found: str
    coverage_limitations: tuple[str, ...]


@dataclass(frozen=True)
class ResearchEvidence:
    research_evidence_id: str
    cluster_id: str
    entity: str
    ticker: str | None
    market: str
    issuer_identity: str
    related_entity: str | None
    relationship_type: RelationshipType
    source: ResearchSource
    event_at: str
    published_at: str
    retrieved_at: str
    research_cutoff: str
    market_session: str
    causal_window_end: str
    evidence_type: EvidenceType
    statement: str
    fact_semantic: str
    causal_time_eligible: bool
    currentness_role: CurrentnessRole
    supports_scopes: tuple[HypothesisScope, ...] = ()
    contradicts_scopes: tuple[HypothesisScope, ...] = ()
    corroboration_refs: tuple[str, ...] = ()
    contradiction_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    negative_scope: NegativeEvidenceScope | None = None


@dataclass(frozen=True)
class ResearchDerivedRelation:
    relation_id: str
    semantic: str
    input_refs: tuple[str, ...]
    formula: str
    period: str
    unit: str
    result: str
    statement: str = ""


@dataclass(frozen=True)
class ResearchHypothesis:
    hypothesis_id: str
    hypothesis_type: EventClusterType
    description: str
    supporting_evidence_refs: tuple[str, ...]
    contradicting_evidence_refs: tuple[str, ...]
    unresolved_questions: tuple[str, ...]
    causal_time_valid: bool
    scope: HypothesisScope
    attribution_strength: AttributionStrength
    what_would_change_the_view: tuple[str, ...]


@dataclass(frozen=True)
class ObservedMove:
    security: str
    ticker: str | None
    market: str
    session: str
    close_return: str
    move_completed_at: str
    intraday_shape: str | None = None


@dataclass(frozen=True)
class EventAttribution:
    event_attribution_version: str
    attribution_id: str
    observed_move: ObservedMove
    primary_hypothesis: str
    secondary_hypotheses: tuple[str, ...]
    rejected_or_weak_hypotheses: tuple[str, ...]
    company_specific_findings: tuple[str, ...]
    sector_findings: tuple[str, ...]
    market_breadth_findings: tuple[str, ...]
    positioning_findings: tuple[str, ...]
    macro_findings: tuple[str, ...]
    negative_evidence: tuple[str, ...]
    unknowns: tuple[str, ...]
    next_confirmation_events: tuple[str, ...]


@dataclass(frozen=True)
class ResearchClaim:
    claim_id: str
    text: str
    support_type: ResearchSupportType
    evidence_refs: tuple[str, ...]
    relation_refs: tuple[str, ...]
    hypothesis_refs: tuple[str, ...]
    materiality_reason: str
    boundary: str


@dataclass(frozen=True)
class ResearchSidecar:
    contract: str
    benchmark_id: str
    production_packet_ref: str
    production_packet_sha256: str
    market: str
    research_cutoff: str
    sources: tuple[ResearchSource, ...]
    search_log: tuple[SearchLogEntry, ...]
    evidence: tuple[ResearchEvidence, ...]
    derived_relations: tuple[ResearchDerivedRelation, ...]
    hypotheses: tuple[ResearchHypothesis, ...]
    attributions: tuple[EventAttribution, ...]
    claims: tuple[ResearchClaim, ...]
    no_material_value_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchValidationIssue:
    code: str
    object_id: str
    detail: str


@dataclass(frozen=True)
class ResearchValidation:
    status: str
    issues: tuple[ResearchValidationIssue, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchAdaptiveDecision:
    renderer: ResearchRenderer
    direct_required_reasons: tuple[str, ...]
    selection_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ResearchShadowResult:
    contract: str
    benchmark_id: str
    status: str
    value_add: str
    decision: ResearchAdaptiveDecision
    final_text: str
    claim_provenance: tuple[dict[str, object], ...]
    validation: dict[str, object]
    production_mutation: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_TIER_ALIASES = {
    "tier1": SourceTier.TIER_1_PRIMARY,
    "tier_1": SourceTier.TIER_1_PRIMARY,
    "primary": SourceTier.TIER_1_PRIMARY,
    "tier2": SourceTier.TIER_2_INDEPENDENT,
    "tier_2": SourceTier.TIER_2_INDEPENDENT,
    "independent": SourceTier.TIER_2_INDEPENDENT,
    "tier3": SourceTier.TIER_3_SECONDARY,
    "tier_3": SourceTier.TIER_3_SECONDARY,
    "secondary": SourceTier.TIER_3_SECONDARY,
    "tier4": SourceTier.TIER_4_LEAD_ONLY,
    "tier_4": SourceTier.TIER_4_LEAD_ONLY,
    "lead": SourceTier.TIER_4_LEAD_ONLY,
}
_CAUSAL_CERTAINTY = re.compile(
    r"(?:원인이다|때문임이\s*확실|확실한\s*원인|증명한다|proves? that|definitive cause)",
    re.IGNORECASE,
)
_NEGATIVE_OVERCLAIM = re.compile(
    r"(?:존재하지\s*않|전혀\s*없|없음이\s*확인|does not exist|there (?:is|was) no)",
    re.IGNORECASE,
)
_BOUNDED_NEGATIVE = re.compile(
    r"(?:검색|확인한|찾지\s*못|searched|within .*scope|not found)", re.IGNORECASE
)


def normalize_source_tier(value: str | SourceTier) -> SourceTier:
    if isinstance(value, SourceTier):
        return value
    normalized = value.strip().casefold().replace("-", "_").replace(" ", "_")
    if normalized in _TIER_ALIASES:
        return _TIER_ALIASES[normalized]
    try:
        return SourceTier(value.strip().upper())
    except ValueError as exc:
        raise ValueError(f"unknown source tier: {value}") from exc


def source_family_key(source: ResearchSource) -> str:
    if source.syndicated_from:
        return source.syndicated_from.casefold().strip()
    if source.source_family:
        return source.source_family.casefold().strip()
    host = urlparse(source.source_ref).netloc.casefold().removeprefix("www.")
    return host or source.name.casefold().strip()


def independent_source_count(sources: tuple[ResearchSource, ...]) -> int:
    return len({source_family_key(source) for source in sources})


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def causal_time_eligible(event_at: str, move_completed_at: str) -> bool:
    return _parse_time(event_at) <= _parse_time(move_completed_at)


def deterministic_percentage(
    numerator: str,
    denominator: str,
    *,
    relation_id: str,
    semantic: str,
    input_refs: tuple[str, ...],
    period: str,
    places: int = 2,
    statement_template: str = "",
) -> ResearchDerivedRelation:
    try:
        top = Decimal(numerator)
        bottom = Decimal(denominator)
    except InvalidOperation as exc:
        raise ValueError("research arithmetic requires decimal inputs") from exc
    if bottom == 0:
        raise ValueError("research arithmetic denominator cannot be zero")
    quantizer = Decimal(1).scaleb(-places)
    result = (top / bottom * Decimal(100)).quantize(quantizer)
    return ResearchDerivedRelation(
        relation_id=relation_id,
        semantic=semantic,
        input_refs=input_refs,
        formula="numerator / denominator * 100",
        period=period,
        unit="percent",
        result=f"{result}%",
        statement=statement_template.format(result=f"{result}%") if statement_template else "",
    )


def deterministic_difference(
    left: str,
    right: str,
    *,
    relation_id: str,
    semantic: str,
    input_refs: tuple[str, ...],
    period: str,
    unit: str,
    statement_template: str = "",
) -> ResearchDerivedRelation:
    try:
        result = Decimal(left) - Decimal(right)
    except InvalidOperation as exc:
        raise ValueError("research arithmetic requires decimal inputs") from exc
    normalized = str(result.normalize())
    display_result = f"{normalized}%p" if unit == "percentage_points" else normalized
    return ResearchDerivedRelation(
        relation_id=relation_id,
        semantic=semantic,
        input_refs=input_refs,
        formula="left - right",
        period=period,
        unit=unit,
        result=display_result,
        statement=(
            statement_template.format(result=normalized)
            if statement_template
            else ""
        ),
    )


_SCOPE_DESCRIPTIONS = {
    HypothesisScope.COMPANY: "직접 기업 이벤트가 당일 움직임의 중심 설명이라는 가설",
    HypothesisScope.SECTOR: "동종 업종의 공통 재료가 움직임을 설명한다는 가설",
    HypothesisScope.MARKET: "시장 전반의 위험회피가 움직임을 설명한다는 가설",
    HypothesisScope.POSITIONING: "대형주 수급과 포지셔닝이 움직임을 키웠다는 가설",
    HypothesisScope.MACRO: "금리와 거시 할인율 변화가 움직임을 설명한다는 가설",
}
_SCOPE_CLUSTER = {
    HypothesisScope.COMPANY: EventClusterType.COMPANY_SPECIFIC_CATALYST,
    HypothesisScope.SECTOR: EventClusterType.SECTOR_INDUSTRY_CATALYST,
    HypothesisScope.MARKET: EventClusterType.MARKET_BREADTH_ROTATION,
    HypothesisScope.POSITIONING: EventClusterType.POSITIONING_FLOW,
    HypothesisScope.MACRO: EventClusterType.MACRO_RATES_FX,
}
_STRENGTH_RANK = {
    AttributionStrength.UNRESOLVED: 0,
    AttributionStrength.WEAK: 1,
    AttributionStrength.MODERATE: 2,
    AttributionStrength.STRONG: 3,
}


def build_competing_hypotheses(
    evidence: tuple[ResearchEvidence, ...],
    *,
    hypothesis_prefix: str,
) -> tuple[ResearchHypothesis, ...]:
    rows: list[ResearchHypothesis] = []
    for scope in HypothesisScope:
        supporting = tuple(
            row.research_evidence_id for row in evidence if scope in row.supports_scopes
        )
        contradicting = tuple(
            row.research_evidence_id for row in evidence if scope in row.contradicts_scopes
        )
        support_rows = [row for row in evidence if row.research_evidence_id in supporting]
        source_families = {source_family_key(row.source) for row in support_rows}
        direct_primary = any(
            row.source.tier == SourceTier.TIER_1_PRIMARY
            and row.relationship_type == RelationshipType.DIRECT_ISSUER
            and row.evidence_type == EvidenceType.CONFIRMED_EVENT_FACT
            and row.causal_time_eligible
            for row in support_rows
        )
        independent_interpretation = any(
            row.source.tier == SourceTier.TIER_2_INDEPENDENT
            and row.evidence_type == EvidenceType.REPORTED_INTERPRETATION
            for row in support_rows
        )
        if not supporting:
            strength = AttributionStrength.UNRESOLVED
        elif contradicting:
            strength = AttributionStrength.WEAK
        elif scope == HypothesisScope.COMPANY and direct_primary and independent_interpretation:
            strength = AttributionStrength.MODERATE
        elif scope in {HypothesisScope.SECTOR, HypothesisScope.MARKET} and len(
            source_families
        ) >= 2:
            strength = AttributionStrength.MODERATE
        else:
            strength = AttributionStrength.WEAK
        rows.append(
            ResearchHypothesis(
                hypothesis_id=f"{hypothesis_prefix}-{scope.value}",
                hypothesis_type=_SCOPE_CLUSTER[scope],
                description=_SCOPE_DESCRIPTIONS[scope],
                supporting_evidence_refs=supporting,
                contradicting_evidence_refs=contradicting,
                unresolved_questions=(
                    ()
                    if supporting
                    else (f"{scope.value} 가설을 확인할 독립 근거가 부족합니다.",)
                ),
                causal_time_valid=all(row.causal_time_eligible for row in support_rows),
                scope=scope,
                attribution_strength=strength,
                what_would_change_the_view=(
                    "동일 시간대의 직접 공식 이벤트 또는 반대 방향의 교차 단면 근거",
                ),
            )
        )
    return tuple(rows)


def build_event_attribution(
    observed_move: ObservedMove,
    hypotheses: tuple[ResearchHypothesis, ...],
    evidence: tuple[ResearchEvidence, ...],
    *,
    attribution_id: str,
) -> EventAttribution:
    priority = {
        HypothesisScope.COMPANY: 5,
        HypothesisScope.SECTOR: 4,
        HypothesisScope.MARKET: 3,
        HypothesisScope.POSITIONING: 2,
        HypothesisScope.MACRO: 1,
    }
    ranked = sorted(
        hypotheses,
        key=lambda row: (
            _STRENGTH_RANK[row.attribution_strength],
            len(row.supporting_evidence_refs) - len(row.contradicting_evidence_refs),
            priority[row.scope],
        ),
        reverse=True,
    )
    primary = ranked[0]
    secondary = tuple(
        row.hypothesis_id
        for row in ranked[1:]
        if row.attribution_strength in {AttributionStrength.MODERATE, AttributionStrength.WEAK}
        and row.supporting_evidence_refs
    )
    rejected = tuple(
        row.hypothesis_id
        for row in ranked[1:]
        if row.attribution_strength == AttributionStrength.UNRESOLVED
        or row.contradicting_evidence_refs
    )

    def findings(scope: HypothesisScope) -> tuple[str, ...]:
        return tuple(
            row.research_evidence_id
            for row in evidence
            if scope in row.supports_scopes
            and row.evidence_type != EvidenceType.NEGATIVE_EVIDENCE
        )

    return EventAttribution(
        event_attribution_version=CONTRACT_VERSION,
        attribution_id=attribution_id,
        observed_move=observed_move,
        primary_hypothesis=primary.hypothesis_id,
        secondary_hypotheses=secondary,
        rejected_or_weak_hypotheses=rejected,
        company_specific_findings=findings(HypothesisScope.COMPANY),
        sector_findings=findings(HypothesisScope.SECTOR),
        market_breadth_findings=findings(HypothesisScope.MARKET),
        positioning_findings=findings(HypothesisScope.POSITIONING),
        macro_findings=findings(HypothesisScope.MACRO),
        negative_evidence=tuple(
            row.research_evidence_id
            for row in evidence
            if row.evidence_type == EvidenceType.NEGATIVE_EVIDENCE
        ),
        unknowns=tuple(
            row.statement for row in evidence if row.evidence_type == EvidenceType.UNKNOWN
        ),
        next_confirmation_events=tuple(
            row.research_evidence_id
            for row in evidence
            if row.currentness_role == CurrentnessRole.UPCOMING_EVENT
        ),
    )


def build_research_claims(
    attribution: EventAttribution,
    hypotheses: tuple[ResearchHypothesis, ...],
    evidence: tuple[ResearchEvidence, ...],
    relations: tuple[ResearchDerivedRelation, ...],
    *,
    claim_prefix: str,
) -> tuple[ResearchClaim, ...]:
    hypothesis_by_id = {row.hypothesis_id: row for row in hypotheses}
    primary = hypothesis_by_id[attribution.primary_hypothesis]
    scope_conclusions = {
        HypothesisScope.COMPANY: (
            "직접 기업 이벤트와 당일 반응이 함께 확인되지만, 기대 실망은 공식 사실이 "
            "아니라 보도된 해석이므로 회사 고유 설명을 중간 강도로 둡니다."
        ),
        HypothesisScope.SECTOR: (
            "직접 기업 악재보다 동종 업종과 대형주에 번진 움직임의 설명력이 더 크지만, "
            "하나의 원인으로 확정하지 않습니다."
        ),
        HypothesisScope.MARKET: (
            "교차 단면 근거는 시장 전반 위험회피보다 특정 대형주·업종에 집중된 움직임을 "
            "더 지지합니다."
        ),
        HypothesisScope.POSITIONING: (
            "확인된 수급은 움직임을 키운 정황이지만 사업 변화의 원인으로 승격하지 않습니다."
        ),
        HypothesisScope.MACRO: (
            "거시 환경은 보조 맥락이지만 종목 움직임의 직접 원인으로 확정할 근거는 부족합니다."
        ),
    }
    claims: list[ResearchClaim] = [
        ResearchClaim(
            claim_id=f"{claim_prefix}-primary",
            text=scope_conclusions[primary.scope],
            support_type=ResearchSupportType.EVENT_ATTRIBUTION_INFERENCE,
            evidence_refs=primary.supporting_evidence_refs,
            relation_refs=(),
            hypothesis_refs=(primary.hypothesis_id,),
            materiality_reason="discriminates the leading cause class",
            boundary="Attribution strength remains explicit and does not become certainty.",
        )
    ]
    direct_candidates = [
        row
        for row in evidence
        if row.evidence_type == EvidenceType.CONFIRMED_EVENT_FACT
        and row.source.tier == SourceTier.TIER_1_PRIMARY
        and primary.scope in row.supports_scopes
    ]
    if direct_candidates:
        row = direct_candidates[0]
        claims.append(
            ResearchClaim(
                claim_id=f"{claim_prefix}-direct",
                text=row.statement,
                support_type=ResearchSupportType.RESEARCH_DIRECT_FACT,
                evidence_refs=(row.research_evidence_id,),
                relation_refs=(),
                hypothesis_refs=(primary.hypothesis_id,),
                materiality_reason="preserves the exact official event boundary",
                boundary="Official event fact only.",
            )
        )
    interpretation = next(
        (
            row
            for row in evidence
            if row.evidence_type == EvidenceType.REPORTED_INTERPRETATION
            and primary.scope in row.supports_scopes
        ),
        None,
    )
    if interpretation is not None:
        claims.append(
            ResearchClaim(
                claim_id=f"{claim_prefix}-reported-interpretation",
                text=interpretation.statement,
                support_type=ResearchSupportType.RESEARCH_REPORTED_INTERPRETATION,
                evidence_refs=(interpretation.research_evidence_id,),
                relation_refs=(),
                hypothesis_refs=(primary.hypothesis_id,),
                materiality_reason="keeps reported interpretation distinct from official fact",
                boundary="Attributed interpretation, not issuer fact.",
            )
        )
    for relation in relations[:2]:
        if not relation.statement:
            continue
        claims.append(
            ResearchClaim(
                claim_id=f"{claim_prefix}-{relation.relation_id}",
                text=relation.statement,
                support_type=ResearchSupportType.MARKET_BREADTH_SYNTHESIS,
                evidence_refs=relation.input_refs,
                relation_refs=(relation.relation_id,),
                hypothesis_refs=tuple(
                    row.hypothesis_id
                    for row in hypotheses
                    if row.scope == HypothesisScope.MARKET
                ),
                materiality_reason="uses deterministic cross-sectional arithmetic",
                boundary="Breadth relation does not prove a single cause.",
            )
        )
    negative = next(
        (row for row in evidence if row.evidence_type == EvidenceType.NEGATIVE_EVIDENCE),
        None,
    )
    if negative is not None:
        claims.append(
            ResearchClaim(
                claim_id=f"{claim_prefix}-negative",
                text=negative.statement,
                support_type=ResearchSupportType.NEGATIVE_EVIDENCE_BOUNDARY,
                evidence_refs=(negative.research_evidence_id,),
                relation_refs=(),
                hypothesis_refs=tuple(
                    row.hypothesis_id
                    for row in hypotheses
                    if row.scope in negative.contradicts_scopes
                ),
                materiality_reason="narrows the explanation without asserting universal absence",
                boundary="Searched-scope negative evidence only.",
            )
        )
    upcoming = next(
        (row for row in evidence if row.currentness_role == CurrentnessRole.UPCOMING_EVENT),
        None,
    )
    if upcoming is not None:
        claims.append(
            ResearchClaim(
                claim_id=f"{claim_prefix}-next",
                text=upcoming.statement,
                support_type=ResearchSupportType.UPCOMING_EVENT_CHECK,
                evidence_refs=(upcoming.research_evidence_id,),
                relation_refs=(),
                hypothesis_refs=(),
                materiality_reason="identifies a verified next disconfirming event",
                boundary="Upcoming event is not a forecast of direction.",
            )
        )
    return tuple(claims)


def _validate_search_budget(sidecar: ResearchSidecar) -> list[ResearchValidationIssue]:
    issues: list[ResearchValidationIssue] = []
    clusters: dict[str, list[SearchLogEntry]] = {}
    for row in sidecar.search_log:
        clusters.setdefault(row.research_cluster_id, []).append(row)
    for cluster_id, rows in clusters.items():
        roots = sum(row.parent_query is None for row in rows)
        followup_rounds = len({row.parent_query for row in rows if row.parent_query})
        if roots > 6 or followup_rounds > 3 or len(rows) > 18:
            issues.append(
                ResearchValidationIssue(
                    "search_budget_exceeded",
                    cluster_id,
                    f"roots={roots} followups={followup_rounds} total={len(rows)}",
                )
            )
    return issues


def validate_research_sidecar(sidecar: ResearchSidecar) -> ResearchValidation:
    issues = _validate_search_budget(sidecar)
    evidence = {row.research_evidence_id: row for row in sidecar.evidence}
    relations = {row.relation_id: row for row in sidecar.derived_relations}
    hypotheses = {row.hypothesis_id: row for row in sidecar.hypotheses}
    source_ids = {row.source_id for row in sidecar.sources}

    if sidecar.contract != CONTRACT_VERSION:
        issues.append(
            ResearchValidationIssue("contract_mismatch", sidecar.benchmark_id, sidecar.contract)
        )
    if not sidecar.production_packet_ref or not sidecar.production_packet_sha256:
        issues.append(
            ResearchValidationIssue(
                "immutable_packet_identity_missing", sidecar.benchmark_id, "packet ref/SHA required"
            )
        )

    for row in sidecar.evidence:
        if row.source.source_id not in source_ids:
            issues.append(
                ResearchValidationIssue(
                    "source_registry_missing", row.research_evidence_id, row.source.source_id
                )
            )
        expected_causal = causal_time_eligible(row.event_at, row.causal_window_end)
        if row.causal_time_eligible != expected_causal:
            issues.append(
                ResearchValidationIssue(
                    "causal_time_mismatch",
                    row.research_evidence_id,
                    f"expected={expected_causal}",
                )
            )
        if row.relationship_type != RelationshipType.DIRECT_ISSUER and (
            row.fact_semantic.startswith("issuer_direct_")
        ):
            issues.append(
                ResearchValidationIssue(
                    "related_entity_promoted_to_direct_issuer",
                    row.research_evidence_id,
                    row.relationship_type,
                )
            )
        if row.evidence_type == EvidenceType.NEGATIVE_EVIDENCE:
            scope = row.negative_scope
            if scope is None or not scope.query_count or not scope.coverage_limitations:
                issues.append(
                    ResearchValidationIssue(
                        "negative_evidence_scope_missing", row.research_evidence_id, row.statement
                    )
                )
            if _NEGATIVE_OVERCLAIM.search(row.statement) or not _BOUNDED_NEGATIVE.search(
                row.statement
            ):
                issues.append(
                    ResearchValidationIssue(
                        "negative_evidence_overclaim", row.research_evidence_id, row.statement
                    )
                )
        if row.source.tier == SourceTier.TIER_4_LEAD_ONLY and row.evidence_type in {
            EvidenceType.CONFIRMED_EVENT_FACT,
            EvidenceType.CONFIRMED_MARKET_FACT,
            EvidenceType.CONFIRMED_FLOW_FACT,
            EvidenceType.CONFIRMED_BREADTH_FACT,
        }:
            issues.append(
                ResearchValidationIssue(
                    "tier4_confirmed_fact", row.research_evidence_id, row.source.source_ref
                )
            )

    for row in sidecar.derived_relations:
        missing = [ref for ref in row.input_refs if ref not in evidence]
        if not row.input_refs or missing:
            issues.append(
                ResearchValidationIssue(
                    "derived_relation_input_missing", row.relation_id, ",".join(missing)
                )
            )

    for row in sidecar.hypotheses:
        all_refs = (*row.supporting_evidence_refs, *row.contradicting_evidence_refs)
        missing = [ref for ref in all_refs if ref not in evidence and ref not in relations]
        unsupported_empty = (
            not row.supporting_evidence_refs
            and row.attribution_strength != AttributionStrength.UNRESOLVED
        )
        if unsupported_empty or missing:
            issues.append(
                ResearchValidationIssue(
                    "hypothesis_evidence_missing", row.hypothesis_id, ",".join(missing)
                )
            )
        if row.attribution_strength == AttributionStrength.STRONG:
            direct_primary = any(
                ref in evidence
                and evidence[ref].source.tier == SourceTier.TIER_1_PRIMARY
                and evidence[ref].relationship_type == RelationshipType.DIRECT_ISSUER
                and evidence[ref].causal_time_eligible
                for ref in row.supporting_evidence_refs
            )
            if not direct_primary:
                issues.append(
                    ResearchValidationIssue(
                        "strong_attribution_without_direct_primary",
                        row.hypothesis_id,
                        row.description,
                    )
                )
        if row.scope in {HypothesisScope.MACRO, HypothesisScope.SECTOR} and (
            row.attribution_strength == AttributionStrength.STRONG
            and len(row.supporting_evidence_refs) == 1
        ):
            issues.append(
                ResearchValidationIssue(
                    "correlation_promoted_to_cause", row.hypothesis_id, row.description
                )
            )

    for row in sidecar.attributions:
        refs = (
            row.primary_hypothesis,
            *row.secondary_hypotheses,
            *row.rejected_or_weak_hypotheses,
        )
        missing = [ref for ref in refs if ref not in hypotheses]
        if missing:
            issues.append(
                ResearchValidationIssue(
                    "attribution_hypothesis_missing", row.attribution_id, ",".join(missing)
                )
            )

    for claim in sidecar.claims:
        missing_evidence = [ref for ref in claim.evidence_refs if ref not in evidence]
        missing_relations = [ref for ref in claim.relation_refs if ref not in relations]
        missing_hypotheses = [ref for ref in claim.hypothesis_refs if ref not in hypotheses]
        if not (claim.evidence_refs or claim.relation_refs or claim.hypothesis_refs):
            missing_evidence.append("no_support")
        if missing_evidence or missing_relations or missing_hypotheses:
            issues.append(
                ResearchValidationIssue(
                    "research_claim_provenance_missing",
                    claim.claim_id,
                    ",".join((*missing_evidence, *missing_relations, *missing_hypotheses)),
                )
            )
            continue
        source_text = "\n".join(evidence[ref].statement for ref in claim.evidence_refs)
        source_text += "\n" + "\n".join(relations[ref].result for ref in claim.relation_refs)
        source_numbers = numeric_tokens(source_text)
        unsupported = [token for token in numeric_tokens(claim.text) if token not in source_numbers]
        if unsupported:
            issues.append(
                ResearchValidationIssue(
                    "unsupported_research_numeric_claim", claim.claim_id, ",".join(unsupported)
                )
            )
        if _CAUSAL_CERTAINTY.search(claim.text):
            issues.append(
                ResearchValidationIssue(
                    "unsupported_causal_certainty", claim.claim_id, claim.text
                )
            )
        if claim.support_type == ResearchSupportType.NEGATIVE_EVIDENCE_BOUNDARY and (
            _NEGATIVE_OVERCLAIM.search(claim.text) or not _BOUNDED_NEGATIVE.search(claim.text)
        ):
            issues.append(
                ResearchValidationIssue(
                    "negative_evidence_claim_overreach", claim.claim_id, claim.text
                )
            )

    return ResearchValidation(status="PASS" if not issues else "FAIL", issues=tuple(issues))


def select_research_renderer(sidecar: ResearchSidecar) -> ResearchAdaptiveDecision:
    if sidecar.no_material_value_reason or not sidecar.claims:
        return ResearchAdaptiveDecision(
            renderer=ResearchRenderer.EXISTING_NO_RESEARCH,
            direct_required_reasons=(),
            selection_reasons=("open_research_value_add_no_material_value",),
        )
    direct_reasons: list[str] = []
    support_types = {claim.support_type for claim in sidecar.claims}
    if ResearchSupportType.NEGATIVE_EVIDENCE_BOUNDARY in support_types:
        direct_reasons.append("material_negative_evidence_boundary")
    if ResearchSupportType.EVENT_ATTRIBUTION_INFERENCE in support_types and len(
        {hypothesis.scope for hypothesis in sidecar.hypotheses}
    ) > 1:
        direct_reasons.append("material_competing_hypotheses")
    if any(
        evidence.currentness_role == CurrentnessRole.AFTER_MOVE_INTERPRETATION
        for evidence in sidecar.evidence
    ):
        direct_reasons.append("causal_time_qualification")
    if {HypothesisScope.COMPANY, HypothesisScope.SECTOR}.issubset(
        {hypothesis.scope for hypothesis in sidecar.hypotheses}
    ):
        direct_reasons.append("company_sector_distinction")
    if direct_reasons:
        return ResearchAdaptiveDecision(
            renderer=ResearchRenderer.DIRECT_ANALYST,
            direct_required_reasons=tuple(dict.fromkeys(direct_reasons)),
            selection_reasons=("direct_required_to_preserve_research_boundaries",),
        )
    return ResearchAdaptiveDecision(
        renderer=ResearchRenderer.CONCISE_HYBRID,
        direct_required_reasons=(),
        selection_reasons=("single_supported_research_conclusion",),
    )


def _preamble(current_text: str) -> str:
    rows = current_text.strip().splitlines()
    kept: list[str] = []
    for row in rows:
        if row.startswith(("🎯", "🔎", "⚖️", "📌", "📈", "💰", "📊", "📐", "⚠️")):
            break
        kept.append(row)
    return "\n".join(kept).strip()


def _render_claims(
    current_text: str, sidecar: ResearchSidecar, renderer: ResearchRenderer
) -> str:
    if renderer == ResearchRenderer.EXISTING_NO_RESEARCH:
        return current_text
    claims = list(sidecar.claims)
    if renderer == ResearchRenderer.CONCISE_HYBRID:
        primary = claims[:1]
        next_check = [
            claim
            for claim in claims
            if claim.support_type == ResearchSupportType.UPCOMING_EVENT_CHECK
        ][:1]
        claims = [*primary, *next_check]
    headings = {
        ResearchSupportType.EVENT_ATTRIBUTION_INFERENCE: "🎯 오늘 움직임의 성격",
        ResearchSupportType.RESEARCH_DIRECT_FACT: "🔎 가장 강한 근거",
        ResearchSupportType.RESEARCH_REPORTED_INTERPRETATION: "🔎 보도된 해석",
        ResearchSupportType.MARKET_BREADTH_SYNTHESIS: "📊 시장 구조",
        ResearchSupportType.CROSS_SECTIONAL_SYNTHESIS: "⚖️ 비교 해석",
        ResearchSupportType.NEGATIVE_EVIDENCE_BOUNDARY: "⚖️ 남은 경계",
        ResearchSupportType.UPCOMING_EVENT_CHECK: "📌 다음 확인",
    }
    grouped: dict[str, list[str]] = {}
    for claim in claims:
        heading = headings[claim.support_type]
        body = (
            f"• {claim.text}"
            if claim.support_type == ResearchSupportType.UPCOMING_EVENT_CHECK
            else claim.text
        )
        grouped.setdefault(heading, []).append(body)
    blocks = [f"{heading}\n" + "\n".join(bodies) for heading, bodies in grouped.items()]
    return "\n\n".join(value for value in (_preamble(current_text), *blocks) if value)


def run_open_research_shadow(
    current_text: str,
    sidecar: ResearchSidecar,
) -> ResearchShadowResult:
    validation = validate_research_sidecar(sidecar)
    if validation.status != "PASS":
        return ResearchShadowResult(
            contract=CONTRACT_VERSION,
            benchmark_id=sidecar.benchmark_id,
            status="FALLBACK",
            value_add="FAIL",
            decision=ResearchAdaptiveDecision(
                renderer=ResearchRenderer.EXISTING_NO_RESEARCH,
                direct_required_reasons=(),
                selection_reasons=("research_validation_failed",),
            ),
            final_text=current_text,
            claim_provenance=(),
            validation=validation.to_dict(),
            production_mutation=0,
        )
    decision = select_research_renderer(sidecar)
    final_text = _render_claims(current_text, sidecar, decision.renderer)
    provenance = tuple(
        {
            "claim_id": claim.claim_id,
            "support_type": claim.support_type,
            "evidence_refs": claim.evidence_refs,
            "relation_refs": claim.relation_refs,
            "hypothesis_refs": claim.hypothesis_refs,
            "boundary": claim.boundary,
        }
        for claim in sidecar.claims
    )
    value_add = (
        "NO_MATERIAL_VALUE"
        if decision.renderer == ResearchRenderer.EXISTING_NO_RESEARCH
        else "PASS"
    )
    return ResearchShadowResult(
        contract=CONTRACT_VERSION,
        benchmark_id=sidecar.benchmark_id,
        status="PASS",
        value_add=value_add,
        decision=decision,
        final_text=final_text,
        claim_provenance=provenance,
        validation=validation.to_dict(),
        production_mutation=0,
    )
