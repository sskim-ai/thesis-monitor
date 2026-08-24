from __future__ import annotations

import inspect
from dataclasses import replace

from app.services.open_research_event_attribution_shadow_service import (
    CONTRACT_VERSION,
    AttributionStrength,
    CurrentnessRole,
    EvidenceType,
    HypothesisScope,
    NegativeEvidenceScope,
    ObservedMove,
    RelationshipType,
    ResearchClaim,
    ResearchEvidence,
    ResearchRenderer,
    ResearchSidecar,
    ResearchSource,
    ResearchSupportType,
    SearchLogEntry,
    SourceTier,
    SourceType,
    build_competing_hypotheses,
    build_event_attribution,
    build_research_claims,
    causal_time_eligible,
    deterministic_percentage,
    independent_source_count,
    normalize_source_tier,
    run_open_research_shadow,
    select_research_renderer,
    source_family_key,
    validate_research_sidecar,
)


CUTOFF = "2026-08-24T16:00:00+09:00"
MOVE_END = "2026-08-24T15:30:00+09:00"


def _source(
    source_id: str,
    *,
    tier: SourceTier = SourceTier.TIER_1_PRIMARY,
    source_type: SourceType = SourceType.ISSUER_OFFICIAL,
    family: str | None = None,
    syndicated_from: str | None = None,
) -> ResearchSource:
    return ResearchSource(
        source_id=source_id,
        name=source_id,
        tier=tier,
        source_type=source_type,
        source_ref=f"https://{source_id}.example/report",
        source_family=family or source_id,
        original_source=source_id,
        syndicated_from=syndicated_from,
        independent_confirmation=syndicated_from is None,
    )


def _evidence(
    evidence_id: str,
    source: ResearchSource,
    *,
    evidence_type: EvidenceType,
    statement: str,
    relationship: RelationshipType = RelationshipType.DIRECT_ISSUER,
    supports: tuple[HypothesisScope, ...] = (),
    contradicts: tuple[HypothesisScope, ...] = (),
    event_at: str = "2026-08-24T08:00:00+09:00",
    currentness: CurrentnessRole = CurrentnessRole.PRE_SESSION_EVENT,
    negative_scope: NegativeEvidenceScope | None = None,
) -> ResearchEvidence:
    return ResearchEvidence(
        research_evidence_id=evidence_id,
        cluster_id="cluster",
        entity="Issuer",
        ticker="AAA",
        market="KR",
        issuer_identity="issuer-aaa",
        related_entity=None,
        relationship_type=relationship,
        source=source,
        event_at=event_at,
        published_at=event_at,
        retrieved_at="2026-08-25T02:00:00+09:00",
        research_cutoff=CUTOFF,
        market_session="2026-08-24 KR regular",
        causal_window_end=MOVE_END,
        evidence_type=evidence_type,
        statement=statement,
        fact_semantic="issuer_direct_event" if relationship == RelationshipType.DIRECT_ISSUER else "context",
        causal_time_eligible=causal_time_eligible(event_at, MOVE_END),
        currentness_role=currentness,
        supports_scopes=supports,
        contradicts_scopes=contradicts,
        negative_scope=negative_scope,
    )


def _built_sidecar(*, market: str = "KR") -> ResearchSidecar:
    official = _source("official")
    wire = _source(
        "wire",
        tier=SourceTier.TIER_2_INDEPENDENT,
        source_type=SourceType.WIRE_NEWS,
    )
    scope = NegativeEvidenceScope(
        question="Was there a new order cut?",
        searched_source_tiers=(
            SourceTier.TIER_1_PRIMARY,
            SourceTier.TIER_2_INDEPENDENT,
        ),
        query_count=2,
        searched_time_window="2026-08-20/2026-08-24",
        entities_or_sectors_checked=("Issuer", "Sector"),
        last_search_at="2026-08-25T02:00:00+09:00",
        what_was_not_found="new order cut",
        coverage_limitations=("public indexed sources only",),
    )
    evidence = (
        _evidence(
            "e-official",
            official,
            evidence_type=EvidenceType.CONFIRMED_EVENT_FACT,
            statement="회사는 장 시작 전에 공식 정책을 발표했습니다.",
            supports=(HypothesisScope.COMPANY,),
        ),
        _evidence(
            "e-wire",
            wire,
            evidence_type=EvidenceType.REPORTED_INTERPRETATION,
            statement="독립 보도는 정책의 구체성 부족을 시장 해석으로 전했습니다.",
            supports=(HypothesisScope.COMPANY,),
        ),
        _evidence(
            "e-breadth",
            wire,
            evidence_type=EvidenceType.CONFIRMED_BREADTH_FACT,
            statement="상승 종목 6개와 하락 종목 4개가 확인됐습니다.",
            relationship=RelationshipType.MARKET_STRUCTURE,
            supports=(HypothesisScope.MARKET,),
            contradicts=(HypothesisScope.MARKET,),
        ),
        _evidence(
            "e-negative",
            wire,
            evidence_type=EvidenceType.NEGATIVE_EVIDENCE,
            statement="검색한 공식·주요 보도 범위에서는 신규 주문 축소 근거를 찾지 못했습니다.",
            relationship=RelationshipType.SECTOR,
            contradicts=(HypothesisScope.SECTOR,),
            negative_scope=scope,
        ),
        _evidence(
            "e-upcoming",
            official,
            evidence_type=EvidenceType.CONFIRMED_EVENT_FACT,
            statement="다음 공식 이사회가 후속 확인 일정입니다.",
            supports=(),
            event_at="2026-08-30T09:00:00+09:00",
            currentness=CurrentnessRole.UPCOMING_EVENT,
        ),
    )
    relation = deterministic_percentage(
        "6",
        "10",
        relation_id="r-breadth",
        semantic="advancer_share",
        input_refs=("e-breadth",),
        period="2026-08-24",
        statement_template="상승 종목 비중은 결정론적으로 {result}였습니다.",
    )
    hypotheses = build_competing_hypotheses(evidence, hypothesis_prefix="h")
    move = ObservedMove(
        security="Issuer",
        ticker="AAA",
        market=market,
        session="2026-08-24 regular",
        close_return="-8.70%",
        move_completed_at=MOVE_END,
    )
    attribution = build_event_attribution(
        move, hypotheses, evidence, attribution_id="a-issuer"
    )
    claims = build_research_claims(
        attribution,
        hypotheses,
        evidence,
        (relation,),
        claim_prefix="c",
    )
    return ResearchSidecar(
        contract=CONTRACT_VERSION,
        benchmark_id=f"benchmark-{market.casefold()}",
        production_packet_ref="immutable-packet",
        production_packet_sha256="a" * 64,
        market=market,
        research_cutoff=CUTOFF,
        sources=(official, wire),
        search_log=(
            SearchLogEntry(
                research_cluster_id="cluster",
                query="official policy",
                created_at="2026-08-25T02:00:00+09:00",
                reason="test company catalyst",
                parent_query=None,
                result_count=2,
                selected_sources=("official", "wire"),
                rejected_sources=(),
            ),
        ),
        evidence=evidence,
        derived_relations=(relation,),
        hypotheses=hypotheses,
        attributions=(attribution,),
        claims=claims,
    )


def test_source_tier_normalization() -> None:
    assert normalize_source_tier("primary") == SourceTier.TIER_1_PRIMARY
    assert normalize_source_tier("tier-2") == SourceTier.TIER_2_INDEPENDENT


def test_duplicate_and_syndicated_source_detection() -> None:
    original = _source("wire", family="wire-family")
    copy = _source(
        "publisher",
        tier=SourceTier.TIER_2_INDEPENDENT,
        family="publisher",
        syndicated_from="wire-family",
    )
    assert source_family_key(original) == source_family_key(copy)
    assert independent_source_count((original, copy)) == 1


def test_entity_identity_related_company_is_not_direct_issuer() -> None:
    sidecar = _built_sidecar()
    related = replace(
        sidecar.evidence[0],
        relationship_type=RelationshipType.CUSTOMER,
        related_entity="Customer",
    )
    result = validate_research_sidecar(
        replace(sidecar, evidence=(related, *sidecar.evidence[1:]))
    )
    assert "related_entity_promoted_to_direct_issuer" in {
        issue.code for issue in result.issues
    }


def test_causal_time_eligibility_and_after_move_rejection() -> None:
    assert causal_time_eligible("2026-08-24T14:00:00+09:00", MOVE_END)
    assert not causal_time_eligible("2026-08-24T16:00:00+09:00", MOVE_END)
    sidecar = _built_sidecar()
    invalid = replace(
        sidecar.evidence[0],
        event_at="2026-08-24T17:00:00+09:00",
        causal_time_eligible=True,
    )
    result = validate_research_sidecar(
        replace(sidecar, evidence=(invalid, *sidecar.evidence[1:]))
    )
    assert "causal_time_mismatch" in {issue.code for issue in result.issues}


def test_negative_evidence_scope_is_required() -> None:
    sidecar = _built_sidecar()
    rows = list(sidecar.evidence)
    rows[3] = replace(rows[3], negative_scope=None)
    result = validate_research_sidecar(replace(sidecar, evidence=tuple(rows)))
    assert "negative_evidence_scope_missing" in {issue.code for issue in result.issues}


def test_negative_evidence_overclaim_is_rejected() -> None:
    sidecar = _built_sidecar()
    rows = list(sidecar.evidence)
    rows[3] = replace(rows[3], statement="신규 주문 축소는 전혀 없습니다.")
    result = validate_research_sidecar(replace(sidecar, evidence=tuple(rows)))
    assert "negative_evidence_overclaim" in {issue.code for issue in result.issues}


def test_competing_hypothesis_structure_contains_all_required_scopes() -> None:
    sidecar = _built_sidecar()
    assert {row.scope for row in sidecar.hypotheses} == set(HypothesisScope)
    assert all(row.what_would_change_the_view for row in sidecar.hypotheses)


def test_cause_vs_correlation_rejects_strong_macro_single_source() -> None:
    sidecar = _built_sidecar()
    macro = next(row for row in sidecar.hypotheses if row.scope == HypothesisScope.MACRO)
    unsafe = replace(
        macro,
        supporting_evidence_refs=("e-breadth",),
        attribution_strength=AttributionStrength.STRONG,
    )
    hypotheses = tuple(unsafe if row == macro else row for row in sidecar.hypotheses)
    result = validate_research_sidecar(replace(sidecar, hypotheses=hypotheses))
    codes = {issue.code for issue in result.issues}
    assert "correlation_promoted_to_cause" in codes


def test_market_breadth_synthesis_uses_deterministic_arithmetic() -> None:
    sidecar = _built_sidecar()
    assert sidecar.derived_relations[0].result == "60.00%"
    assert sidecar.derived_relations[0].input_refs == ("e-breadth",)
    assert validate_research_sidecar(sidecar).status == "PASS"


def test_hidden_research_arithmetic_is_rejected() -> None:
    sidecar = _built_sidecar()
    unsafe = ResearchClaim(
        claim_id="hidden",
        text="상승 종목 비중은 75%였습니다.",
        support_type=ResearchSupportType.MARKET_BREADTH_SYNTHESIS,
        evidence_refs=("e-breadth",),
        relation_refs=(),
        hypothesis_refs=(),
        materiality_reason="negative control",
        boundary="none",
    )
    result = validate_research_sidecar(replace(sidecar, claims=(unsafe,)))
    assert "unsupported_research_numeric_claim" in {
        issue.code for issue in result.issues
    }


def test_source_attribution_and_claim_provenance_are_preserved() -> None:
    sidecar = _built_sidecar()
    result = run_open_research_shadow("Header\n\n🎯 old", sidecar)
    assert result.status == "PASS"
    assert result.claim_provenance
    assert all(row["evidence_refs"] or row["relation_refs"] for row in result.claim_provenance)
    assert "보도는" in result.final_text


def test_research_free_analyst_and_adaptive_direct_required() -> None:
    sidecar = _built_sidecar()
    decision = select_research_renderer(sidecar)
    assert decision.renderer == ResearchRenderer.DIRECT_ANALYST
    assert "material_negative_evidence_boundary" in decision.direct_required_reasons
    assert "material_competing_hypotheses" in decision.direct_required_reasons


def test_no_value_research_preserves_existing_message() -> None:
    sidecar = _built_sidecar()
    empty = replace(
        sidecar,
        evidence=(),
        derived_relations=(),
        hypotheses=(),
        attributions=(),
        claims=(),
        no_material_value_reason="no material public event",
    )
    current = "Existing validated message"
    result = run_open_research_shadow(current, empty)
    assert result.value_add == "NO_MATERIAL_VALUE"
    assert result.final_text == current


def test_kr_and_us_use_same_market_abstraction() -> None:
    kr = _built_sidecar(market="KR")
    us = _built_sidecar(market="US")
    assert validate_research_sidecar(kr).status == "PASS"
    assert validate_research_sidecar(us).status == "PASS"
    assert select_research_renderer(kr).renderer == select_research_renderer(us).renderer


def test_source_tier4_cannot_confirm_event_fact() -> None:
    sidecar = _built_sidecar()
    lead = _source(
        "lead",
        tier=SourceTier.TIER_4_LEAD_ONLY,
        source_type=SourceType.COMMUNITY_LEAD,
    )
    rows = list(sidecar.evidence)
    rows[0] = replace(rows[0], source=lead)
    result = validate_research_sidecar(
        replace(sidecar, sources=(*sidecar.sources, lead), evidence=tuple(rows))
    )
    assert "tier4_confirmed_fact" in {issue.code for issue in result.issues}


def test_search_budget_is_fail_closed() -> None:
    sidecar = _built_sidecar()
    rows = tuple(
        replace(sidecar.search_log[0], query=f"query {index}") for index in range(19)
    )
    result = validate_research_sidecar(replace(sidecar, search_log=rows))
    assert "search_budget_exceeded" in {issue.code for issue in result.issues}


def test_attribution_builder_selects_supported_company_hypothesis() -> None:
    sidecar = _built_sidecar()
    attribution = sidecar.attributions[0]
    primary = next(
        row for row in sidecar.hypotheses if row.hypothesis_id == attribution.primary_hypothesis
    )
    assert primary.scope == HypothesisScope.COMPANY
    assert primary.attribution_strength == AttributionStrength.MODERATE


def test_reported_interpretation_is_not_promoted_to_official_fact() -> None:
    sidecar = _built_sidecar()
    reported = next(
        row
        for row in sidecar.claims
        if row.support_type == ResearchSupportType.RESEARCH_REPORTED_INTERPRETATION
    )
    assert reported.evidence_refs == ("e-wire",)
    assert "official" not in reported.claim_id


def test_production_isolation_has_no_runtime_delivery_imports() -> None:
    source = inspect.getsource(run_open_research_shadow)
    module = inspect.getmodule(run_open_research_shadow)
    module_source = inspect.getsource(module)
    assert "Telegram" not in source
    assert "recordThesisAssessment" not in module_source
    assert "notificationdelivery" not in module_source.casefold()
    assert "app.jobs" not in module_source


def test_holdout_scheduler_is_not_embedded_in_research_runtime() -> None:
    module = inspect.getmodule(run_open_research_shadow)
    source = inspect.getsource(module)
    assert "apscheduler" not in source.casefold()
    assert "launchctl" not in source.casefold()
    assert "automation_update" not in source


def test_failure_falls_back_to_existing_message_without_mutation() -> None:
    sidecar = _built_sidecar()
    broken = replace(sidecar, production_packet_sha256="")
    current = "Existing validated message"
    result = run_open_research_shadow(current, broken)
    assert result.status == "FALLBACK"
    assert result.final_text == current
    assert result.production_mutation == 0


def test_contract_does_not_contain_ticker_or_market_specific_logic() -> None:
    module = inspect.getmodule(run_open_research_shadow)
    source = inspect.getsource(module)
    assert all(value not in source for value in ("005930", "000660", "GOOGL", "NVDA"))
