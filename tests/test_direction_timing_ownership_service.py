from __future__ import annotations

from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.direction_timing_ownership_service import (
    CORE_DOMAINS,
    TIMING_DOMAINS,
    CoreHolderView,
    CoreNewBuyerView,
    DirectionalClaim,
    DirectionalCoreCandidate,
    DirectionalSellDriver,
    DirectionalUnknown,
    EvidenceDomain,
    HolderPriceReview,
    PriceTimingCandidate,
    TechnicalState,
    TimingNewBuyerModifier,
    TimingClaim,
    build_owned_evidence_packet,
    compose_decision,
    core_fingerprint,
    stage_alias_catalogs,
    technical_feature_inventory,
    validate_directional_core_ownership,
    validate_ownership,
)
from app.services.directional_balance_service import DirectionalBalance


def _ref(
    ref_id: str,
    category: EvidenceCategory,
    source_ref: str,
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=category,
        label=ref_id,
        statement=ref_id,
        source_ref=source_ref,
    )


def _packet() -> tuple[DecisionEvidencePacket, dict[str, object]]:
    fundamental = "canonical:fundamental:TEST:business_current:abc"
    earnings = "canonical:fundamental:TEST:earnings_financial_current:def"
    evidence = (
        _ref(
            fundamental,
            EvidenceCategory.EARNINGS_QUALITY,
            "stock.fact_catalog.fundamental:TEST:business_current:abc",
        ),
        _ref(
            earnings,
            EvidenceCategory.EARNINGS,
            "stock.fact_catalog.fundamental:TEST:earnings_financial_current:def",
        ),
        _ref(
            "canonical:price:current",
            EvidenceCategory.PRICE_STRUCTURE,
            "stock.fact_catalog.price:current",
        ),
        _ref(
            "canonical:chart:structure:state",
            EvidenceCategory.PRICE_STRUCTURE,
            "stock.fact_catalog.chart:structure:state",
        ),
        _ref(
            "technical-feature:rsi",
            EvidenceCategory.TECHNICAL_FEATURE,
            "technical_context.ctx.daily.rsi_14",
        ),
        _ref(
            "technical-feature:macd",
            EvidenceCategory.TECHNICAL_FEATURE,
            "technical_context.ctx.weekly.macd_histogram",
        ),
        _ref(
            "technical-feature:bollinger",
            EvidenceCategory.TECHNICAL_FEATURE,
            "technical_context.ctx.monthly.bollinger_20_2_state",
        ),
        _ref(
            "technical-feature:volume",
            EvidenceCategory.TECHNICAL_FEATURE,
            "technical_context.ctx.daily.volume_ratio_20",
        ),
        _ref(
            "decision-evidence:supply",
            EvidenceCategory.FLOWS,
            "stock.supply_context",
        ),
    )
    packet = DecisionEvidencePacket(
        packet_id="packet-1",
        ticker="TEST",
        company_name="Test",
        market="us",
        assessment_date="2026-09-06",
        horizon="12m",
        evidence=evidence,
        prohibited_claims=(),
        evidence_sha256="evidence-sha",
    )
    stock = {
        "fact_catalog": [
            {
                "fact_id": "fundamental:TEST:business_current:abc",
                "evidence_family": "BUSINESS_CURRENT",
            },
            {
                "fact_id": "fundamental:TEST:earnings_financial_current:def",
                "evidence_family": "EARNINGS_FINANCIAL_CURRENT",
            },
            {"fact_id": "price:current", "evidence_family": "PRICE_CONTEXT"},
            {"fact_id": "chart:structure:state", "evidence_family": "PRICE_CONTEXT"},
        ]
    }
    return packet, stock


def _claim(text: str, ref: str) -> DirectionalClaim:
    return DirectionalClaim(text=text, evidence_refs=(ref,))


def _core(
    *,
    decision: str = "HOLD",
    buyer: str = "ATTRACTIVE",
    holder: str = "HOLDABLE",
) -> DirectionalCoreCandidate:
    fundamental = "canonical:fundamental:TEST:business_current:abc"
    earnings = "canonical:fundamental:TEST:earnings_financial_current:def"
    balance = {
        "BUY": DirectionalBalance(buy=6, sell=4),
        "HOLD": DirectionalBalance(buy=5, sell=5),
        "SELL": DirectionalBalance(buy=4, sell=6),
    }[decision]
    hold_lean = "NEUTRAL" if decision == "HOLD" else "NOT_HOLD"
    return DirectionalCoreCandidate(
        ticker="TEST",
        overall_direction=decision,
        directional_balance=balance,
        hold_lean=hold_lean,
        directional_confidence="MEDIUM",
        business_thesis_change="UNCHANGED",
        business_thesis_context=_claim("Business evidence.", fundamental),
        earnings_estimate_context=_claim("Earnings evidence.", earnings),
        market_expectation_context=_claim("Expectations remain uncertain.", fundamental),
        valuation_context=_claim("Valuation remains uncertain.", fundamental),
        risk_context=_claim("Business risk remains.", fundamental),
        sector_interpretation=_claim("Sector context applies.", fundamental),
        buy_drivers=(_claim("Business support.", fundamental),),
        sell_drivers=(
            DirectionalSellDriver(
                text="Business risk.",
                evidence_refs=(fundamental,),
                classification="STRUCTURAL_RISK",
            ),
        ),
        dominant_evidence=_claim("Business evidence dominates.", fundamental),
        uncertainty_limit=_claim("Evidence is limited.", fundamental),
        core_investment_judgment=_claim("Core judgment.", fundamental),
        unknown_treatments=(
            DirectionalUnknown(
                summary="A remaining unknown.",
                evidence_refs=(fundamental,),
                treatment="CONFIDENCE_LIMIT",
                directional_negative_basis=(),
            ),
        ),
        material_directional_anchor_basis=(earnings,),
        fundamental_new_buyer=CoreNewBuyerView(
            stance=buyer,
            summary="Fundamental entry stance.",
            confirmation_business_condition="Business confirmation is needed.",
            confirmation_business_condition_refs=(fundamental,),
        ),
        fundamental_holder=CoreHolderView(
            stance=holder,
            summary="Fundamental holder stance.",
            business_invalidation_condition="Business deterioration invalidates the case.",
            business_invalidation_condition_refs=(fundamental,),
        ),
        business_reevaluation_up=(_claim("Business improves.", fundamental),),
        business_reevaluation_down=(_claim("Business deteriorates.", fundamental),),
    )


def _timing(
    core: DirectionalCoreCandidate,
    *,
    modifier: TimingNewBuyerModifier = TimingNewBuyerModifier.ALLOW,
    review: HolderPriceReview = HolderPriceReview.NONE,
    state: TechnicalState = TechnicalState.FAVORABLE,
) -> PriceTimingCandidate:
    price = "canonical:price:current"
    technical = "technical-feature:rsi"
    return PriceTimingCandidate(
        ticker="TEST",
        core_fingerprint=core_fingerprint(core),
        technical_state=state,
        timing_new_buyer_modifier=modifier,
        entry_mode="NONE",
        entry_reason="No verified entry level is available.",
        pullback_entry_zone_low=None,
        pullback_entry_zone_high=None,
        pullback_entry_basis=(),
        breakout_confirmation_level=None,
        breakout_confirmation_basis=(),
        confirmation_semantics="NONE",
        holder_price_review=review,
        upside_trim_zone_low=None,
        upside_trim_zone_high=None,
        upside_trim_basis=(),
        downside_review_level=None,
        downside_review_basis=(),
        currency="USD",
        price_review_context=TimingClaim(text="Price review context.", evidence_refs=(price,)),
        price_confirmation_context=TimingClaim(
            text="No confirmation level.", evidence_refs=(technical,)
        ),
        price_support_context=TimingClaim(
            text="No support level.", evidence_refs=(technical,)
        ),
        technical_rationale=TimingClaim(text="Technical state.", evidence_refs=(technical,)),
        supply_positioning_rationale=None,
    )


def test_domain_registry_hard_fences_core_and_timing() -> None:
    packet, stock = _packet()
    owned = build_owned_evidence_packet(packet, stock=stock)
    domains = owned.domain_by_ref
    assert domains["canonical:fundamental:TEST:business_current:abc"] == EvidenceDomain.BUSINESS_CURRENT
    assert domains["canonical:price:current"] == EvidenceDomain.PRICE_CONTEXT
    assert domains["technical-feature:volume"] == EvidenceDomain.VOLUME_LIQUIDITY
    assert domains["decision-evidence:supply"] == EvidenceDomain.SUPPLY_POSITIONING
    assert all(domains[ref] in CORE_DOMAINS for ref in owned.core_refs)
    assert all(domains[ref] in TIMING_DOMAINS for ref in owned.timing_refs)
    core_aliases, timing_aliases = stage_alias_catalogs(owned)
    assert set(core_aliases.by_ref) == set(owned.core_refs)
    assert set(timing_aliases.by_ref) == set(owned.timing_refs)


def test_counterfactual_price_state_cannot_mutate_direction_balance_or_lean() -> None:
    packet, stock = _packet()
    owned = build_owned_evidence_packet(packet, stock=stock)
    core = _core(decision="HOLD")
    favorable = compose_decision(core, _timing(core))
    adverse = compose_decision(
        core,
        _timing(
            core,
            modifier=TimingNewBuyerModifier.AVOID,
            review=HolderPriceReview.REVIEW,
            state=TechnicalState.ADVERSE,
        ),
    )
    for result in (favorable, adverse):
        assert result.candidate.decision == "HOLD"
        assert result.candidate.directional_balance == DirectionalBalance(buy=5, sell=5)
        assert validate_ownership(owned, core, result.timing, result).valid
    assert favorable.candidate.new_buyer_view.stance == "ATTRACTIVE"
    assert adverse.candidate.new_buyer_view.stance == "AVOID"
    assert adverse.candidate.holder_view.stance == "REVIEW"


def test_timing_only_downgrades_new_buyer_and_never_creates_reduce() -> None:
    packet, stock = _packet()
    owned = build_owned_evidence_packet(packet, stock=stock)
    for core_stance, expected in (
        ("ATTRACTIVE", "AVOID"),
        ("WAIT", "AVOID"),
        ("AVOID", "AVOID"),
    ):
        core = _core(buyer=core_stance, holder="HOLDABLE")
        timing = _timing(
            core,
            modifier=TimingNewBuyerModifier.AVOID,
            review=HolderPriceReview.REVIEW,
        )
        composed = compose_decision(core, timing)
        assert composed.candidate.new_buyer_view.stance == expected
        assert composed.candidate.holder_view.stance == "REVIEW"
        assert validate_ownership(owned, core, timing, composed).valid


def test_sell_requires_nonprice_material_anchor() -> None:
    packet, stock = _packet()
    owned = build_owned_evidence_packet(packet, stock=stock)
    core = _core(decision="SELL").model_copy(
        update={"material_directional_anchor_basis": ()}
    )
    timing = _timing(core, state=TechnicalState.ADVERSE)
    composed = compose_decision(core, timing)
    validation = validate_ownership(owned, core, timing, composed)
    assert not validation.valid
    assert validation.sell_without_nonprice_material_anchor == 1


def test_directional_core_rejects_price_and_supply_refs() -> None:
    packet, stock = _packet()
    owned = build_owned_evidence_packet(packet, stock=stock)
    core = _core().model_copy(
        update={
            "material_directional_anchor_basis": (
                "canonical:price:current",
                "decision-evidence:supply",
            )
        }
    )
    timing = _timing(core)
    validation = validate_ownership(owned, core, timing)
    assert not validation.valid
    assert validation.directional_core_price_technical_refs == 1
    assert validation.directional_core_supply_refs == 1


def test_core_only_validator_reuses_domain_fences_and_stage_catalog() -> None:
    packet, stock = _packet()
    owned = build_owned_evidence_packet(packet, stock=stock)
    core_catalog, _ = stage_alias_catalogs(owned)
    valid = validate_directional_core_ownership(
        owned,
        _core(decision="BUY"),
        allowed_core_ref_ids=tuple(core_catalog.by_ref),
    )
    invalid_core = _core().model_copy(
        update={"material_directional_anchor_basis": ("canonical:price:current",)}
    )
    invalid = validate_directional_core_ownership(
        owned,
        invalid_core,
        allowed_core_ref_ids=tuple(core_catalog.by_ref),
    )

    assert valid.valid
    assert not invalid.valid
    assert invalid.directional_core_price_technical_refs == 1
    assert invalid.directional_core_unknown_refs == 1


def test_technical_inventory_preserves_unavailable_distinct_from_neutral() -> None:
    packet, stock = _packet()
    owned = build_owned_evidence_packet(packet, stock=stock)
    inventory = technical_feature_inventory(owned)
    assert inventory["rsi"] is True
    assert inventory["macd"] is True
    assert inventory["bollinger"] is True
    assert inventory["volume"] is True
    assert inventory["invented_feature_count"] == 0
    assert inventory["unavailable_is_zero"] is False


def test_business_invalidation_is_copied_only_from_core() -> None:
    packet, stock = _packet()
    owned = build_owned_evidence_packet(packet, stock=stock)
    core = _core(decision="BUY")
    timing = _timing(
        core,
        modifier=TimingNewBuyerModifier.WAIT,
        review=HolderPriceReview.REVIEW,
        state=TechnicalState.ADVERSE,
    )
    composed = compose_decision(core, timing)
    assert (
        composed.candidate.holder_view.business_invalidation_condition
        == core.fundamental_holder.business_invalidation_condition
    )
    assert composed.candidate.decision == "BUY"
    assert validate_ownership(owned, core, timing, composed).valid
