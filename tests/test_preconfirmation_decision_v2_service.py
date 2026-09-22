from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts import v2_production_cutover_preflight as preflight
from app.jobs import accepted_decision_v2_runtime as accepted_v2_runtime_job

from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
    EvidenceClaim,
)
from app.services.evidence_maturity_pricing_service import (
    DriverEvidenceMaturity,
    DriverEvidenceMaturityV2,
    EvidenceMaturity,
    MarketExpectation,
    MarketExpectationAssessment,
    MaturityProvenanceStatus,
    OverallMaturityAssessment,
    PricingRequirement,
    PricingRequirementAssessment,
    project_maturity_provenance,
    symbolic_maturity_evidence_kind,
)
from app.services.preconfirmation_decision_v2_service import (
    FactualSafetyState,
    PostconfirmationHoldExplanation,
    PreconfirmationBuyExplanation,
    PreconfirmationDecisionCandidate,
    preconfirmation_stage2_field_ownership_inventory,
    preconfirmation_message_quality,
    requires_preconfirmation_buy,
    render_preconfirmation_shadow,
    validate_preconfirmation_candidate,
    validate_preconfirmation_stage2_owned_semantics,
)
from app.services.scenario_asymmetry_service import (
    Asymmetry,
    AsymmetryAssessment,
    ConfirmationCost,
    ConfirmationCostAssessment,
    PreconfirmationErrorCost,
    PreconfirmationErrorCostAssessment,
    ScenarioInterpretation,
    ScenarioName,
    ScenarioSet,
)
from app.services.accepted_decision_v2_service import (
    AcceptedDecisionFrozenCoreNumericScope,
    AcceptedDecisionSource,
    AcceptedDecisionStatus,
    AcceptedV2Adjudication,
    accepted_message_quality,
    decision_change_condition_errors,
    normalize_decision_change_condition,
    render_accepted_v2_production,
    render_accepted_v2_shadow,
    resolve_accepted_v2_decision,
    validate_accepted_v2_decision,
    validate_accepted_v2_render,
)
from app.services.accepted_decision_v2_runtime_service import (
    STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT,
    STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT,
    STAGE2_MODEL_OUTPUT_CONTRACT,
    STAGE2_MODEL_OUTPUT_CONTRACT_V2,
    STAGE2_MODEL_OUTPUT_CONTRACT_V3,
    AcceptedV2EvidenceOwnership,
    AcceptedV2FundamentalCoreBatch,
    AcceptedV2ProductionBaseline,
    AcceptedV2ProductionBatchOutput,
    AcceptedV2ProductionBatchOutputV2,
    AcceptedV2ProductionArtifactV2,
    AcceptedV2ProductionBlock,
    AcceptedV2ProductionContext,
    accepted_v2_fundamental_core_from_candidate,
    accepted_v2_fundamental_core_sha256,
    accepted_v2_stage2_validation_scope_manifest,
    accepted_v2_stage2_output_schema,
    build_accepted_v2_production_context,
    materialize_accepted_v2_stage2_output,
    load_accepted_v2_production_artifact,
    parse_accepted_v2_production_batch_output,
    Stage2MaturityAsOfMaterializationError,
    validate_accepted_v2_candidate_ownership,
    validate_accepted_v2_fundamental_core,
    validate_accepted_v2_maturity_atomic_identity,
    validate_accepted_v2_production_output,
    validate_accepted_v2_stage2_candidate,
)
from app.services.decision_canary_service import canonical_sha256
from app.services.expectation_valuation_interaction_service import interaction_from_packet
from app.services.accepted_decision_consistency_service import (
    MaterialEvidenceDelta,
    audit_accepted_decision_consistency,
)
from app.services.directional_balance_service import (
    DirectionalBalance,
    decision_from_directional_balance,
    render_directional_balance,
)
from app.services.three_axis_decision_service import (
    HolderDecisionAxis,
    NewBuyerDecisionAxis,
)
from app.services.stage2_maturity_polarity_adapter_service import (
    maturity_atomic_claim_ref,
)


def _claim(ref: str, text: str = "검증된 근거가 이 해석을 지지합니다.") -> EvidenceClaim:
    return EvidenceClaim(text=text, evidence_refs=(ref,))


def _packet() -> DecisionEvidencePacket:
    categories = {
        "thesis": EvidenceCategory.THESIS,
        "earnings": EvidenceCategory.EARNINGS,
        "expectations": EvidenceCategory.EXPECTATIONS,
        "valuation": EvidenceCategory.VALUATION,
        "risks": EvidenceCategory.RISKS,
        "market": EvidenceCategory.MARKET,
        "price": EvidenceCategory.PRICE_STRUCTURE,
        "quality": EvidenceCategory.QUALITY,
        "unknown": EvidenceCategory.UNKNOWN,
    }
    return DecisionEvidencePacket(
        packet_id="packet-v2",
        ticker="TEST",
        company_name="테스트기업",
        market="us",
        assessment_date="2026-08-30",
        horizon="장기",
        evidence=tuple(
            DecisionEvidenceRef(
                ref_id=f"ref:{name}",
                category=category,
                label=name,
                statement=f"{name} canonical evidence",
                as_of="2026-08-30",
                source_ref="fixture",
            )
            for name, category in categories.items()
        ),
        prohibited_claims=(),
        evidence_sha256="fixture",
    )


def _scenario(name: ScenarioName) -> ScenarioInterpretation:
    return ScenarioInterpretation(
        scenario=name,
        business_and_earnings=_claim("ref:earnings", f"{name} 사업과 이익 가정입니다."),
        expectation_and_valuation=_claim("ref:valuation", f"{name} 기대와 평가 가정입니다."),
        macro_market_conditions=_claim("ref:market", f"{name} 시장 조건입니다."),
    )


def _candidate() -> PreconfirmationDecisionCandidate:
    buy_driver = _claim("ref:valuation", "보수적 평가가 매수 방향을 지지합니다.")
    sell_driver = _claim("ref:risks", "실행 위험이 매도 방향의 반대 근거입니다.")
    candidate = PreconfirmationDecisionCandidate(
        ticker="TEST",
        fundamental_core_sha256="0" * 64,
        decision="BUY",
        new_buyer_axis=NewBuyerDecisionAxis(
            stance="ATTRACTIVE",
            reason=_claim("ref:price", "현재 진입 가격 구조는 부담이 크지 않습니다."),
        ),
        holder_axis=HolderDecisionAxis(
            stance="HOLDABLE",
            reason=_claim("ref:thesis", "기존 사업 근거는 보유 유지와 양립합니다."),
        ),
        directional_balance=DirectionalBalance(buy=6, sell=4),
        buy_drivers=(buy_driver,),
        sell_drivers=(sell_driver,),
        balance_summary="낮은 기대와 실행 위험을 함께 반영해 매수 우위가 있습니다.",
        reasoning_grade="VERY_HIGH",
        confidence="MEDIUM",
        timing="NEUTRAL",
        timing_basis=_claim("ref:price", "가격 구조는 단기 진입을 막지 않습니다."),
        factual_safety_state=FactualSafetyState.PASS,
        factual_safety_basis=_claim("ref:quality", "핵심 사실 기준은 검증됐습니다."),
        driver_maturity=(
            DriverEvidenceMaturity(
                driver="신규 제품 수익화",
                decisive=True,
                maturity=EvidenceMaturity.PARTIAL,
                supporting_evidence_refs=("ref:valuation",),
                contradicting_evidence_refs=("ref:risks",),
                supporting_claim_refs=(
                    maturity_atomic_claim_ref(ticker="TEST", claim=buy_driver),
                ),
                contradicting_claim_refs=(
                    maturity_atomic_claim_ref(ticker="TEST", claim=sell_driver),
                ),
                what_remains_unproven=_claim(
                    "ref:unknown", "반복 가능한 경제성은 아직 확인되지 않았습니다."
                ),
                as_of="2026-08-30",
            ),
        ),
        overall_maturity=OverallMaturityAssessment(
            maturity=EvidenceMaturity.PARTIAL,
            basis=_claim("ref:thesis", "방향성은 보이지만 경제성 증명은 부분적입니다."),
        ),
        market_expectation=MarketExpectationAssessment(
            level=MarketExpectation.LOW,
            basis=_claim("ref:expectations", "시장 기대는 낮은 편으로 해석됩니다."),
        ),
        pricing_requirement=PricingRequirementAssessment(
            requirement=PricingRequirement.CONSERVATIVE_OUTCOME_SUFFICIENT,
            basis=_claim("ref:valuation", "강한 낙관 없이도 현재 평가를 설명할 수 있습니다."),
            valuation_basis=_claim("ref:valuation", "검증된 평가 근거를 사용했습니다."),
            expectation_basis=_claim("ref:expectations", "낮은 기대가 불확실성을 반영합니다."),
            key_assumption=_claim("ref:thesis", "기존 사업의 내구성이 핵심 가정입니다."),
            unknowns=(_claim("ref:unknown", "신규 수익화의 반복성은 미확인입니다."),),
        ),
        scenarios=ScenarioSet(
            bear=_scenario(ScenarioName.BEAR),
            base=_scenario(ScenarioName.BASE),
            bull=_scenario(ScenarioName.BULL),
        ),
        asymmetry=AsymmetryAssessment(
            asymmetry=Asymmetry.FAVORABLE,
            basis=_claim("ref:valuation", "보수적 결과 대비 상방 선택지가 더 큽니다."),
            downside_permanence=_claim("ref:risks", "하방의 영구 손실 경로는 제한적입니다."),
            upside_not_priced=_claim("ref:expectations", "상방 가능성은 전부 반영되지 않았습니다."),
        ),
        confirmation_cost=ConfirmationCostAssessment(
            cost=ConfirmationCost.HIGH,
            basis=_claim("ref:expectations", "완전 확인과 가격 재평가가 함께 올 수 있습니다."),
            likely_repricing_channel=_claim("ref:earnings", "이익 추정 개선이 재평가 경로입니다."),
        ),
        preconfirmation_error_cost=PreconfirmationErrorCostAssessment(
            cost=PreconfirmationErrorCost.MEDIUM,
            basis=_claim(
                "ref:risks", "초기 가정 실패의 손실 경로는 관리 가능하지만 남아 있습니다."
            ),
            capital_loss_channel=_claim("ref:quality", "사업 내구성 훼손이 영구 손실 경로입니다."),
        ),
        pre_confirmation_buy=True,
        preconfirmation_buy_explanation=PreconfirmationBuyExplanation(
            not_yet_confirmed=_claim("ref:unknown", "신규 수익화의 반복성은 아직 미확인입니다."),
            directionally_credible=_claim(
                "ref:earnings", "현재 실적 방향은 초기 논리와 일치합니다."
            ),
            market_already_prices=_claim(
                "ref:expectations", "시장은 상당한 불확실성을 반영합니다."
            ),
            favorable_asymmetry=_claim("ref:valuation", "현재 평가는 보수적 결과도 수용합니다."),
            thesis_break_risk=_claim("ref:risks", "기존 사업 훼손은 초기 논리를 깨뜨립니다."),
            buy_to_hold_or_sell=_claim("ref:risks", "방향성 증거가 반전되면 판단을 낮춥니다."),
        ),
        post_confirmation_hold=False,
        postconfirmation_hold_explanation=None,
        decisive_reason=_claim(
            "ref:valuation", "부분 증명 상태지만 현재 기대가 불확실성을 충분히 보상합니다."
        ),
        why_not_buy=_claim("ref:risks", "실행 실패 위험은 BUY 확신도를 제한합니다."),
        why_not_sell=_claim("ref:thesis", "기존 사업과 초기 수익화 방향은 하방 우위를 막습니다."),
        opposing_evidence=(_claim("ref:risks", "실행 반복성은 아직 반대 근거로 남습니다."),),
        unknowns=(_claim("ref:unknown", "경제성의 지속 기간은 확인되지 않았습니다."),),
        upgrade_condition=_claim("ref:earnings", "경제성의 반복 증거가 쌓이면 확신을 높입니다."),
        downgrade_condition=_claim("ref:risks", "기존 사업까지 약화되면 판단을 낮춥니다."),
    )
    core = accepted_v2_fundamental_core_from_candidate(candidate)
    return candidate.model_copy(
        update={"fundamental_core_sha256": accepted_v2_fundamental_core_sha256(core)}
    )


def _candidate_with_current_core_sha(
    candidate: PreconfirmationDecisionCandidate,
) -> PreconfirmationDecisionCandidate:
    core = accepted_v2_fundamental_core_from_candidate(candidate)
    return candidate.model_copy(
        update={"fundamental_core_sha256": accepted_v2_fundamental_core_sha256(core)}
    )


def _candidate_with_frozen_core_numeric_claims() -> PreconfirmationDecisionCandidate:
    candidate = _candidate()
    numeric_buy = candidate.buy_drivers[0].model_copy(
        update={"text": "검증된 평가 12.4172배가 매수 방향을 지지합니다."}
    )
    numeric_sell = candidate.sell_drivers[0].model_copy(
        update={"text": "평가 19.2893배와 12.4172배의 간극은 반대 근거입니다."}
    )
    maturity = candidate.driver_maturity[0].model_copy(
        update={
            "supporting_claim_refs": (
                maturity_atomic_claim_ref(ticker="TEST", claim=numeric_buy),
            ),
            "contradicting_claim_refs": (
                maturity_atomic_claim_ref(ticker="TEST", claim=numeric_sell),
            ),
        }
    )
    return _candidate_with_current_core_sha(
        candidate.model_copy(
            update={
                "buy_drivers": (numeric_buy,),
                "sell_drivers": (numeric_sell,),
                "driver_maturity": (maturity,),
            }
        )
    )


def test_driver_maturity_date_must_be_owned_by_a_cited_ref() -> None:
    candidate = _candidate()
    row = candidate.driver_maturity[0].model_copy(update={"as_of": "2026-08-29"})

    validation = validate_preconfirmation_candidate(
        _packet(),
        candidate.model_copy(update={"driver_maturity": (row,)}),
    )

    assert "maturity_evidence_date_not_owned:신규 제품 수익화" in validation.errors


def test_symbolic_only_maturity_evidence_is_fail_closed() -> None:
    packet = _packet()
    evidence = tuple(
        row.model_copy(update={"as_of": "latest"})
        if row.ref_id == "ref:thesis"
        else row
        for row in packet.evidence
    )
    candidate = _candidate()
    maturity = candidate.driver_maturity[0].model_copy(
        update={
            "supporting_evidence_refs": ("ref:thesis",),
            "contradicting_evidence_refs": (),
        }
    )

    validation = validate_preconfirmation_candidate(
        packet.model_copy(update={"evidence": evidence}),
        candidate.model_copy(update={"driver_maturity": (maturity,)}),
    )

    assert "maturity_evidence_date_unresolvable:신규 제품 수익화" in validation.errors


def _core(candidate: PreconfirmationDecisionCandidate | None = None):
    return accepted_v2_fundamental_core_from_candidate(candidate or _candidate())


def _trusted_core_batch(
    context: AcceptedV2ProductionContext,
    *cores,
) -> AcceptedV2FundamentalCoreBatch:
    return AcceptedV2FundamentalCoreBatch(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        cores=cores,
    )


def _model_facing_stage2_payload(
    output: AcceptedV2ProductionBatchOutput,
) -> dict[str, object]:
    payload = output.model_dump(mode="json")
    payload["contract"] = STAGE2_MODEL_OUTPUT_CONTRACT_V2
    for candidate in payload["candidates"]:
        for row in candidate["driver_maturity"]:
            row.pop("as_of")
    return payload


def _runtime_owned_source_ref_payload(
    output: AcceptedV2ProductionBatchOutput,
) -> dict[str, object]:
    payload = output.model_dump(mode="json")
    payload["contract"] = STAGE2_MODEL_OUTPUT_CONTRACT
    for candidate in payload["candidates"]:
        for row in candidate["driver_maturity"]:
            row.pop("supporting_evidence_refs")
            row.pop("contradicting_evidence_refs")
            row.pop("as_of")
    return payload


def _stage2_materialization_fixture(
    *,
    packet: DecisionEvidencePacket | None = None,
    candidate: PreconfirmationDecisionCandidate | None = None,
) -> tuple[
    AcceptedV2ProductionContext,
    AcceptedV2ProductionBatchOutput,
    dict[str, object],
]:
    source_packet = packet or _packet()
    source_candidate = candidate or _candidate()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": source_packet.packet_id,
            "market": source_packet.market,
            "assessment_date": source_packet.assessment_date,
            "stocks": [{"ticker": source_packet.ticker}],
        },
        claim_id="claim-stage2-materialization",
        evidence_packets=(source_packet,),
    )
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(_core(source_candidate),),
        candidates=(source_candidate,),
    )
    return context, output, _model_facing_stage2_payload(output)


def _materialize_runtime_owned_source_refs(
    context: AcceptedV2ProductionContext,
    output: AcceptedV2ProductionBatchOutput,
    *,
    subjects: tuple[str, ...] | None = None,
) -> AcceptedV2ProductionBatchOutputV2:
    materialized = materialize_accepted_v2_stage2_output(
        context,
        _runtime_owned_source_ref_payload(output),
        fundamental_cores=output.fundamental_cores,
        subjects=subjects,
    )
    assert isinstance(materialized, AcceptedV2ProductionBatchOutputV2)
    return materialized


def test_m12ck_r03_runtime_projects_one_parent_claim_refs() -> None:
    context, output, _raw = _stage2_materialization_fixture()

    materialized = _materialize_runtime_owned_source_refs(context, output)
    row = materialized.candidates[0].driver_maturity[0]

    assert row.supporting_evidence_refs == ("ref:valuation",)
    assert row.contradicting_evidence_refs == ("ref:risks",)


def test_m12ck_r04_runtime_projects_complete_multi_parent_union() -> None:
    candidate = _candidate()
    buy_driver = candidate.buy_drivers[0].model_copy(
        update={"evidence_refs": ("ref:valuation", "ref:thesis")}
    )
    maturity = candidate.driver_maturity[0].model_copy(
        update={
            "supporting_evidence_refs": buy_driver.evidence_refs,
            "supporting_claim_refs": (
                maturity_atomic_claim_ref(ticker="TEST", claim=buy_driver),
            ),
        }
    )
    candidate = _candidate_with_current_core_sha(
        candidate.model_copy(
            update={"buy_drivers": (buy_driver,), "driver_maturity": (maturity,)}
        )
    )
    context, output, _raw = _stage2_materialization_fixture(candidate=candidate)

    materialized = _materialize_runtime_owned_source_refs(context, output)

    assert materialized.candidates[0].driver_maturity[
        0
    ].supporting_evidence_refs == ("ref:valuation", "ref:thesis")


def test_m12ck_r05_projection_preserves_claim_parent_order_and_deduplicates() -> None:
    candidate = _candidate()
    first = candidate.buy_drivers[0].model_copy(
        update={"evidence_refs": ("ref:valuation", "ref:thesis")}
    )
    second = EvidenceClaim(
        text="두 번째 구조화된 상방 주장입니다.",
        evidence_refs=("ref:thesis", "ref:earnings"),
    )
    selected_claim_refs = (
        maturity_atomic_claim_ref(ticker="TEST", claim=second),
        maturity_atomic_claim_ref(ticker="TEST", claim=first),
    )
    maturity = candidate.driver_maturity[0].model_copy(
        update={
            "supporting_evidence_refs": (
                "ref:thesis",
                "ref:earnings",
                "ref:valuation",
            ),
            "supporting_claim_refs": selected_claim_refs,
        }
    )
    candidate = _candidate_with_current_core_sha(
        candidate.model_copy(
            update={
                "buy_drivers": (first, second),
                "driver_maturity": (maturity,),
            }
        )
    )
    context, output, _raw = _stage2_materialization_fixture(candidate=candidate)

    materialized = _materialize_runtime_owned_source_refs(context, output)

    assert materialized.candidates[0].driver_maturity[
        0
    ].supporting_evidence_refs == (
        "ref:thesis",
        "ref:earnings",
        "ref:valuation",
    )


def test_m12ck_r06_cross_ticker_claim_ref_is_rejected_before_provenance() -> None:
    packet = _packet()
    other_packet = packet.model_copy(
        update={"ticker": "OTHER", "company_name": "다른기업", "evidence_sha256": "other"}
    )
    test_candidate = _candidate()
    other_buy = test_candidate.buy_drivers[0]
    other_sell = test_candidate.sell_drivers[0]
    other_maturity = test_candidate.driver_maturity[0].model_copy(
        update={
            "supporting_claim_refs": (
                maturity_atomic_claim_ref(ticker="OTHER", claim=other_buy),
            ),
            "contradicting_claim_refs": (
                maturity_atomic_claim_ref(ticker="OTHER", claim=other_sell),
            ),
        }
    )
    other_candidate = _candidate_with_current_core_sha(
        test_candidate.model_copy(
            update={"ticker": "OTHER", "driver_maturity": (other_maturity,)}
        )
    )
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": "TEST"}, {"ticker": "OTHER"}],
        },
        claim_id="claim-stage2-cross-ticker-atomic",
        evidence_packets=(packet, other_packet),
    )
    cores = (_core(test_candidate), _core(other_candidate))
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=cores,
        candidates=(test_candidate, other_candidate),
    )
    raw = _runtime_owned_source_ref_payload(output)
    raw["candidates"][0]["driver_maturity"][0]["supporting_claim_refs"] = [
        other_maturity.supporting_claim_refs[0]
    ]

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_materialization_cross_ticker_claim_ref:TEST:0",
    ):
        materialize_accepted_v2_stage2_output(
            context,
            raw,
            fundamental_cores=cores,
            subjects=("TEST", "OTHER"),
        )


def test_m12ck_r07_unknown_claim_ref_is_rejected_before_provenance() -> None:
    context, output, _raw = _stage2_materialization_fixture()
    raw = _runtime_owned_source_ref_payload(output)
    raw["candidates"][0]["driver_maturity"][0]["supporting_claim_refs"] = [
        "maturity-claim:" + "f" * 64
    ]

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_materialization_unknown_ticker_local_claim_ref:TEST:0",
    ):
        materialize_accepted_v2_stage2_output(
            context,
            raw,
            fundamental_cores=output.fundamental_cores,
        )


def test_m12ck_r08_same_claim_on_both_sides_is_rejected() -> None:
    context, output, _raw = _stage2_materialization_fixture()
    raw = _runtime_owned_source_ref_payload(output)
    supporting = raw["candidates"][0]["driver_maturity"][0][
        "supporting_claim_refs"
    ][0]
    raw["candidates"][0]["driver_maturity"][0]["contradicting_claim_refs"] = [
        supporting
    ]

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_materialization_atomic_claim_overlap:TEST:0",
    ):
        materialize_accepted_v2_stage2_output(
            context,
            raw,
            fundamental_cores=output.fundamental_cores,
        )


def test_m12ck_r09_model_authored_source_refs_are_rejected() -> None:
    context, output, _raw = _stage2_materialization_fixture()
    raw = _runtime_owned_source_ref_payload(output)
    raw["candidates"][0]["driver_maturity"][0][
        "supporting_evidence_refs"
    ] = ["ref:valuation"]

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_model_authored_source_refs_forbidden:TEST:0",
    ):
        materialize_accepted_v2_stage2_output(
            context,
            raw,
            fundamental_cores=output.fundamental_cores,
        )


def test_m12ck_runtime_rejects_missing_supporting_claim_identity() -> None:
    context, output, _raw = _stage2_materialization_fixture()
    raw = _runtime_owned_source_ref_payload(output)
    raw["candidates"][0]["driver_maturity"][0]["supporting_claim_refs"] = []

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_materialization_supporting_claim_identity_missing:TEST:0",
    ):
        materialize_accepted_v2_stage2_output(
            context,
            raw,
            fundamental_cores=output.fundamental_cores,
        )


def test_m12cl_v4_schema_requires_support_but_allows_empty_contradiction() -> None:
    context, output, _raw = _stage2_materialization_fixture()

    schema = accepted_v2_stage2_output_schema(
        context,
        fundamental_cores=output.fundamental_cores,
    )
    maturity = schema["$defs"]["DriverEvidenceMaturity"]
    properties = maturity["properties"]

    assert STAGE2_MODEL_OUTPUT_CONTRACT == "v2-accepted-stage2-model-output-v4"
    assert schema["properties"]["contract"]["const"] == STAGE2_MODEL_OUTPUT_CONTRACT
    assert properties["supporting_claim_refs"]["minItems"] == 1
    assert "minItems" not in properties["contradicting_claim_refs"]
    assert "supporting_claim_refs" in maturity["required"]
    assert "contradicting_claim_refs" in maturity["required"]


def test_m12cl_v3_historical_raw_output_remains_materializable() -> None:
    context, output, _raw = _stage2_materialization_fixture()
    v4_raw = _runtime_owned_source_ref_payload(output)
    v3_raw = dict(v4_raw)
    v3_raw["contract"] = STAGE2_MODEL_OUTPUT_CONTRACT_V3

    materialized = materialize_accepted_v2_stage2_output(
        context,
        v3_raw,
        fundamental_cores=output.fundamental_cores,
    )
    expected = materialize_accepted_v2_stage2_output(
        context,
        v4_raw,
        fundamental_cores=output.fundamental_cores,
    )

    assert isinstance(materialized, AcceptedV2ProductionBatchOutputV2)
    assert materialized == expected


def test_m12cl_v4_accepts_empty_contradicting_claims() -> None:
    candidate = _candidate()
    maturity = candidate.driver_maturity[0].model_copy(
        update={
            "contradicting_evidence_refs": (),
            "contradicting_claim_refs": (),
        }
    )
    candidate = _candidate_with_current_core_sha(
        candidate.model_copy(update={"driver_maturity": (maturity,)})
    )
    context, output, _raw = _stage2_materialization_fixture(candidate=candidate)

    materialized = _materialize_runtime_owned_source_refs(context, output)
    row = materialized.candidates[0].driver_maturity[0]

    assert row.supporting_claim_refs
    assert row.contradicting_claim_refs == ()
    assert row.contradicting_evidence_refs == ()


def test_m12ck_r10_post_materialization_source_ref_tamper_is_rejected() -> None:
    context, output, _raw = _stage2_materialization_fixture()
    materialized = _materialize_runtime_owned_source_refs(context, output)
    candidate = materialized.candidates[0]
    row = candidate.driver_maturity[0].model_copy(
        update={"supporting_evidence_refs": ("ref:thesis",)}
    )

    errors = validate_accepted_v2_maturity_atomic_identity(
        candidate.model_copy(update={"driver_maturity": (row,)}),
        output.fundamental_cores[0],
    )

    assert "maturity_supporting_source_claim_mismatch:0" in errors


@pytest.mark.parametrize(
    ("case_id", "parent_refs", "expected_as_of", "expected_status"),
    (
        (
            "R11",
            ("canonical:financial_quality:latest",),
            None,
            MaturityProvenanceStatus.SYMBOLIC_ONLY_NO_CONCRETE_DATE,
        ),
        (
            "R12",
            ("ref:valuation", "canonical:financial_quality:latest"),
            "2026-08-30",
            MaturityProvenanceStatus.CONCRETE_WITH_SYMBOLIC_REFS,
        ),
        (
            "R13",
            ("ref:valuation", "ref:thesis"),
            "2026-08-30",
            MaturityProvenanceStatus.CONCRETE_ONLY,
        ),
    ),
)
def test_m12ck_r11_r13_provenance_projection_is_preserved(
    case_id: str,
    parent_refs: tuple[str, ...],
    expected_as_of: str | None,
    expected_status: MaturityProvenanceStatus,
) -> None:
    packet = _packet()
    if "canonical:financial_quality:latest" in parent_refs:
        packet = packet.model_copy(
            update={
                "evidence": (*packet.evidence, _financial_quality_symbolic_ref())
            }
        )
    candidate = _candidate()
    buy_driver = candidate.buy_drivers[0].model_copy(
        update={"evidence_refs": parent_refs}
    )
    maturity = candidate.driver_maturity[0].model_copy(
        update={
            "supporting_evidence_refs": parent_refs,
            "contradicting_evidence_refs": (),
            "supporting_claim_refs": (
                maturity_atomic_claim_ref(ticker="TEST", claim=buy_driver),
            ),
            "contradicting_claim_refs": (),
        }
    )
    candidate = _candidate_with_current_core_sha(
        candidate.model_copy(
            update={"buy_drivers": (buy_driver,), "driver_maturity": (maturity,)}
        )
    )
    context, output, _raw = _stage2_materialization_fixture(
        packet=packet,
        candidate=candidate,
    )

    materialized = _materialize_runtime_owned_source_refs(context, output)
    row = materialized.candidates[0].driver_maturity[0]

    assert case_id in {"R11", "R12", "R13"}
    assert row.as_of == expected_as_of
    assert row.provenance_status == expected_status


@pytest.mark.parametrize("runtime_field", ("as_of", "provenance_status"))
def test_m12ck_r14_model_authored_provenance_fields_are_rejected(
    runtime_field: str,
) -> None:
    context, output, _raw = _stage2_materialization_fixture()
    raw = _runtime_owned_source_ref_payload(output)
    raw["candidates"][0]["driver_maturity"][0][runtime_field] = (
        "2026-08-30" if runtime_field == "as_of" else "CONCRETE_ONLY"
    )

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match=f"stage2_model_authored_{runtime_field}_forbidden",
    ):
        materialize_accepted_v2_stage2_output(
            context,
            raw,
            fundamental_cores=output.fundamental_cores,
        )


def _materialize_v1(
    context: AcceptedV2ProductionContext,
    raw: dict[str, object],
    *,
    subjects: tuple[str, ...] | None = None,
) -> AcceptedV2ProductionBatchOutput:
    output = materialize_accepted_v2_stage2_output(
        context,
        raw,
        subjects=subjects,
        normalized_contract=STAGE2_MATURITY_AS_OF_MATERIALIZATION_CONTRACT,
    )
    assert isinstance(output, AcceptedV2ProductionBatchOutput)
    return output


def _financial_quality_symbolic_ref() -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id="canonical:financial_quality:latest",
        category=EvidenceCategory.EARNINGS,
        label="financial_quality",
        statement=json.dumps(
            {
                "decision_version": "financial-quality-taint-v2",
                "reason_codes": ["provider_not_supported"],
                "source_period": None,
                "source_type": "unknown",
                "state": "unknown",
            },
            sort_keys=True,
        ),
        as_of="latest",
        source_ref="stock.fact_catalog.financial_quality:latest",
    )


def _earnings_symbolic_ref() -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id="canonical:earnings:latest",
        category=EvidenceCategory.EARNINGS,
        label="earnings",
        statement=json.dumps(
            {
                "field_period_labels": {},
                "field_statement_basis": {},
                "financial_period_required": True,
                "period": "latest",
                "period_label": None,
                "period_type": None,
                "preliminary": False,
            },
            sort_keys=True,
        ),
        as_of="latest",
        source_ref="stock.fact_catalog.earnings:latest",
    )


def _symbolic_ref_statement(
    row: DecisionEvidenceRef,
    *,
    remove: tuple[str, ...] = (),
    replace: dict[str, object] | None = None,
) -> DecisionEvidenceRef:
    statement = json.loads(row.statement)
    for field_name in remove:
        statement.pop(field_name, None)
    statement.update(replace or {})
    return row.model_copy(
        update={"statement": json.dumps(statement, sort_keys=True)}
    )


def _materialization_with_refs(
    *refs: str,
    packet: DecisionEvidencePacket | None = None,
) -> tuple[AcceptedV2ProductionContext, dict[str, object]]:
    source_packet = packet or _packet()
    candidate = _candidate()
    maturity = candidate.driver_maturity[0].model_copy(
        update={
            "supporting_evidence_refs": tuple(refs),
            "contradicting_evidence_refs": (),
        }
    )
    context, _output, raw = _stage2_materialization_fixture(
        packet=source_packet,
        candidate=candidate.model_copy(update={"driver_maturity": (maturity,)}),
    )
    return context, raw


def test_m12cg_symbolic_only_provenance_is_materialized_without_fake_date() -> None:
    packet = _packet().model_copy(
        update={"evidence": (*_packet().evidence, _financial_quality_symbolic_ref())}
    )
    context, raw = _materialization_with_refs(
        "canonical:financial_quality:latest",
        packet=packet,
    )

    output = materialize_accepted_v2_stage2_output(context, raw)

    assert isinstance(output, AcceptedV2ProductionBatchOutputV2)
    row = output.candidates[0].driver_maturity[0]
    assert row.as_of is None
    assert (
        row.provenance_status
        == MaturityProvenanceStatus.SYMBOLIC_ONLY_NO_CONCRETE_DATE
    )
    validation = validate_preconfirmation_candidate(packet, output.candidates[0])
    assert not any("maturity_" in error for error in validation.errors)


def test_m12cg_mixed_provenance_uses_concrete_max_and_explicit_status() -> None:
    packet = _packet().model_copy(
        update={"evidence": (*_packet().evidence, _financial_quality_symbolic_ref())}
    )
    context, raw = _materialization_with_refs(
        "ref:valuation",
        "canonical:financial_quality:latest",
        packet=packet,
    )

    output = materialize_accepted_v2_stage2_output(context, raw)

    assert isinstance(output, AcceptedV2ProductionBatchOutputV2)
    row = output.candidates[0].driver_maturity[0]
    assert row.as_of == "2026-08-30"
    assert (
        row.provenance_status
        == MaturityProvenanceStatus.CONCRETE_WITH_SYMBOLIC_REFS
    )


def test_m12cg_concrete_projection_is_order_and_duplicate_invariant() -> None:
    packet = _packet()
    refs = {row.ref_id: row for row in packet.evidence}

    first = project_maturity_provenance(
        refs,
        ("ref:valuation", "ref:risks", "ref:valuation"),
    )
    second = project_maturity_provenance(refs, ("ref:risks", "ref:valuation"))

    assert first == second
    assert first.as_of == "2026-08-30"
    assert first.provenance_status == MaturityProvenanceStatus.CONCRETE_ONLY


def test_m12cg_symbolic_classifier_requires_canonical_structured_metadata() -> None:
    recognized = _financial_quality_symbolic_ref()
    malformed = recognized.model_copy(update={"as_of": " latest "})
    free_text = recognized.model_copy(update={"statement": "unknown latest filing"})

    assert symbolic_maturity_evidence_kind(recognized) is not None
    assert symbolic_maturity_evidence_kind(_earnings_symbolic_ref()) is not None
    assert symbolic_maturity_evidence_kind(malformed) is None
    assert symbolic_maturity_evidence_kind(free_text) is None


def test_m12cg_r2_financial_quality_missing_source_period_is_rejected() -> None:
    invalid_ref = _symbolic_ref_statement(
        _financial_quality_symbolic_ref(),
        remove=("source_period",),
    )
    packet = _packet().model_copy(
        update={"evidence": (*_packet().evidence, invalid_ref)}
    )
    context, raw = _materialization_with_refs(
        invalid_ref.ref_id,
        packet=packet,
    )

    assert symbolic_maturity_evidence_kind(invalid_ref) is None
    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_materialization_unresolvable_provenance",
    ):
        materialize_accepted_v2_stage2_output(context, raw)


@pytest.mark.parametrize(
    ("field_name", "remaining_field"),
    [
        ("period_label", "period_type"),
        ("period_type", "period_label"),
    ],
)
def test_m12cg_r2_earnings_missing_required_nullable_field_is_rejected(
    field_name: str,
    remaining_field: str,
) -> None:
    invalid_ref = _symbolic_ref_statement(
        _earnings_symbolic_ref(),
        remove=(field_name,),
    )
    statement = json.loads(invalid_ref.statement)

    assert remaining_field in statement
    assert statement[remaining_field] is None
    assert symbolic_maturity_evidence_kind(invalid_ref) is None
    projection = project_maturity_provenance(
        {invalid_ref.ref_id: invalid_ref},
        (invalid_ref.ref_id,),
    )
    assert projection.invalid_ref_ids == (invalid_ref.ref_id,)
    assert projection.provenance_status is None


def test_m12cg_r2_earnings_missing_both_nullable_fields_is_rejected() -> None:
    invalid_ref = _symbolic_ref_statement(
        _earnings_symbolic_ref(),
        remove=("period_label", "period_type"),
    )

    assert symbolic_maturity_evidence_kind(invalid_ref) is None


@pytest.mark.parametrize("invalid_value", ["null", "", 0, False, {}, []])
@pytest.mark.parametrize(
    ("row_factory", "field_name"),
    [
        (_financial_quality_symbolic_ref, "source_period"),
        (_earnings_symbolic_ref, "period_label"),
        (_earnings_symbolic_ref, "period_type"),
    ],
)
def test_m12cg_r2_required_nullable_fields_reject_non_null_values(
    row_factory: Callable[[], DecisionEvidenceRef],
    field_name: str,
    invalid_value: object,
) -> None:
    row = row_factory()
    invalid_ref = _symbolic_ref_statement(
        row,
        replace={field_name: invalid_value},
    )

    assert symbolic_maturity_evidence_kind(invalid_ref) is None


def test_m12cg_r2_concrete_peer_cannot_hide_missing_metadata_ref() -> None:
    invalid_ref = _symbolic_ref_statement(
        _financial_quality_symbolic_ref(),
        remove=("source_period",),
    )
    packet = _packet().model_copy(
        update={"evidence": (*_packet().evidence, invalid_ref)}
    )
    context, raw = _materialization_with_refs(
        "ref:valuation",
        invalid_ref.ref_id,
        packet=packet,
    )

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_materialization_unresolvable_provenance",
    ):
        materialize_accepted_v2_stage2_output(context, raw)


def test_m12cg_r2_empty_maturity_ref_set_is_rejected() -> None:
    context, _output, raw = _stage2_materialization_fixture()
    raw["candidates"][0]["driver_maturity"][0][
        "supporting_evidence_refs"
    ] = []
    raw["candidates"][0]["driver_maturity"][0][
        "contradicting_evidence_refs"
    ] = []

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_materialization_unresolvable_provenance:TEST:0:<empty>",
    ):
        materialize_accepted_v2_stage2_output(context, raw)


def test_m12cg_r2_independent_validator_rejects_forged_symbolic_projection() -> None:
    valid_packet = _packet().model_copy(
        update={
            "evidence": (*_packet().evidence, _financial_quality_symbolic_ref())
        }
    )
    context, raw = _materialization_with_refs(
        "canonical:financial_quality:latest",
        packet=valid_packet,
    )
    output = materialize_accepted_v2_stage2_output(context, raw)
    invalid_ref = _symbolic_ref_statement(
        _financial_quality_symbolic_ref(),
        remove=("source_period",),
    )
    invalid_packet = _packet().model_copy(
        update={"evidence": (*_packet().evidence, invalid_ref)}
    )

    validation = validate_preconfirmation_candidate(
        invalid_packet,
        output.candidates[0],
    )

    assert not validation.valid
    assert any(
        error.startswith("maturity_provenance_unresolvable:")
        for error in validation.errors
    )


@pytest.mark.parametrize("market_prefix", ["us_fixture", "kr_fixture"])
def test_m12cg_r2_presence_guard_is_not_ref_or_market_specific(
    market_prefix: str,
) -> None:
    original = _financial_quality_symbolic_ref()
    ref_id = f"canonical:{market_prefix}:financial_quality:latest"
    valid_ref = original.model_copy(
        update={
            "ref_id": ref_id,
            "source_ref": f"stock.fact_catalog.{ref_id.removeprefix('canonical:')}",
        }
    )
    invalid_ref = _symbolic_ref_statement(
        valid_ref,
        remove=("source_period",),
    )

    assert symbolic_maturity_evidence_kind(valid_ref) is not None
    assert symbolic_maturity_evidence_kind(invalid_ref) is None


def test_m12cg_r2_atomic_polarity_mutation_is_rejected() -> None:
    candidate = _candidate()
    original = candidate.driver_maturity[0]
    mutated = original.model_copy(
        update={"supporting_claim_refs": original.contradicting_claim_refs}
    )
    mutated_candidate = candidate.model_copy(
        update={"driver_maturity": (mutated,)}
    )

    errors = validate_accepted_v2_maturity_atomic_identity(
        mutated_candidate,
        _core(candidate),
    )

    assert "maturity_supporting_source_claim_mismatch:0" in errors


def test_m12cg_model_authored_provenance_status_is_rejected() -> None:
    context, _output, raw = _stage2_materialization_fixture()
    raw["candidates"][0]["driver_maturity"][0][
        "provenance_status"
    ] = "CONCRETE_ONLY"

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_model_authored_provenance_status_forbidden",
    ):
        materialize_accepted_v2_stage2_output(context, raw)


def test_m12cg_concrete_ref_cannot_hide_invalid_symbolic_peer() -> None:
    packet = _packet()
    evidence = tuple(
        row.model_copy(update={"as_of": "current"})
        if row.ref_id == "ref:risks"
        else row
        for row in packet.evidence
    )
    context, raw = _materialization_with_refs(
        "ref:valuation",
        "ref:risks",
        packet=packet.model_copy(update={"evidence": evidence}),
    )

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_materialization_unresolvable_provenance",
    ):
        materialize_accepted_v2_stage2_output(context, raw)


@pytest.mark.parametrize("invalid", ["null", "", 0, False])
def test_m12cg_normalized_date_rejects_non_json_null_primitives(invalid: object) -> None:
    payload = _candidate().driver_maturity[0].model_dump(mode="json")
    payload["as_of"] = invalid
    payload["provenance_status"] = "SYMBOLIC_ONLY_NO_CONCRETE_DATE"

    with pytest.raises(ValidationError):
        DriverEvidenceMaturityV2.model_validate(payload)


def test_m12cg_normalized_status_date_shape_is_relationally_strict() -> None:
    payload = _candidate().driver_maturity[0].model_dump(mode="json")
    payload["as_of"] = None
    payload["provenance_status"] = "CONCRETE_ONLY"

    with pytest.raises(ValidationError, match="maturity_provenance_status_date_mismatch"):
        DriverEvidenceMaturityV2.model_validate(payload)


def test_m12cg_hard_validator_recomputes_max_and_status() -> None:
    packet = _packet().model_copy(
        update={"evidence": (*_packet().evidence, _financial_quality_symbolic_ref())}
    )
    context, raw = _materialization_with_refs(
        "ref:valuation",
        "canonical:financial_quality:latest",
        packet=packet,
    )
    output = materialize_accepted_v2_stage2_output(context, raw)
    assert isinstance(output, AcceptedV2ProductionBatchOutputV2)
    candidate = output.candidates[0]
    tampered_row = candidate.driver_maturity[0].model_copy(
        update={"provenance_status": MaturityProvenanceStatus.CONCRETE_ONLY}
    )

    validation = validate_preconfirmation_candidate(
        packet,
        candidate.model_copy(update={"driver_maturity": (tampered_row,)}),
    )

    assert "maturity_provenance_status_mismatch:신규 제품 수익화" in validation.errors


def test_m12cg_raw_stage2_schema_does_not_expose_runtime_provenance_fields() -> None:
    context, _output, _raw = _stage2_materialization_fixture()

    schema = accepted_v2_stage2_output_schema(context)
    maturity = schema["$defs"]["DriverEvidenceMaturity"]

    assert "as_of" not in maturity["properties"]
    assert "provenance_status" not in maturity["properties"]
    assert "as_of" not in maturity["required"]
    assert "provenance_status" not in maturity["required"]


def test_m12cg_version_dispatch_preserves_legacy_and_rejects_unknown_contract() -> None:
    context, _output, raw = _stage2_materialization_fixture()
    legacy = _materialize_v1(context, raw)
    migrated = materialize_accepted_v2_stage2_output(
        context,
        raw,
        normalized_contract=STAGE2_MATURITY_PROVENANCE_MATERIALIZATION_CONTRACT,
    )

    assert parse_accepted_v2_production_batch_output(
        legacy.model_dump(mode="json")
    ) == legacy
    assert parse_accepted_v2_production_batch_output(
        migrated.model_dump(mode="json")
    ) == migrated
    with pytest.raises(ValueError, match="unsupported_accepted_v2_output_contract"):
        parse_accepted_v2_production_batch_output({"contract": "unsupported"})


def test_m12cg_v2_artifact_roundtrip_is_deterministic(
    tmp_path,
) -> None:
    context, _output, raw = _stage2_materialization_fixture()
    output = materialize_accepted_v2_stage2_output(context, raw)
    validated_at = datetime(2026, 9, 16, tzinfo=UTC)

    first = validate_accepted_v2_production_output(
        context,
        output,
        validated_at=validated_at,
    )
    second = validate_accepted_v2_production_output(
        context,
        output,
        validated_at=validated_at,
    )

    assert isinstance(first, AcceptedV2ProductionArtifactV2)
    assert first == second
    path = tmp_path / "accepted-v2.json"
    path.write_text(first.model_dump_json(), encoding="utf-8")
    packet = {
        "packet_id": context.packet_id,
        "market": context.market,
        "assessment_date": context.assessment_date,
        "stocks": [{"ticker": "TEST"}],
    }
    loaded = load_accepted_v2_production_artifact(
        path,
        packet=packet,
        claim_id=context.claim_id,
    )
    assert loaded == first


def test_m12cg_earnings_placeholder_does_not_bypass_atomic_claim_eligibility() -> None:
    packet = _packet().model_copy(
        update={"evidence": (*_packet().evidence, _earnings_symbolic_ref())}
    )
    context, raw = _materialization_with_refs(
        "canonical:earnings:latest",
        packet=packet,
    )
    output = materialize_accepted_v2_stage2_output(context, raw)
    assert isinstance(output, AcceptedV2ProductionBatchOutputV2)

    errors = validate_accepted_v2_maturity_atomic_identity(
        output.candidates[0],
        output.fundamental_cores[0],
    )

    assert "maturity_supporting_source_claim_mismatch:0" in errors


def test_stage2_materializer_uses_max_concrete_same_row_date() -> None:
    packet = _packet()
    evidence = tuple(
        row.model_copy(
            update={
                "as_of": (
                    "2026-06-30" if row.ref_id == "ref:valuation" else row.as_of
                )
            }
        )
        for row in packet.evidence
    )
    context, _output, raw = _stage2_materialization_fixture(
        packet=packet.model_copy(update={"evidence": evidence})
    )

    materialized = _materialize_v1(context, raw)

    assert materialized.contract == "v2-accepted-production-output-v1"
    assert materialized.candidates[0].driver_maturity[0].as_of == "2026-08-30"


def test_stage2_materializer_uses_concrete_date_with_symbolic_peer() -> None:
    packet = _packet()
    evidence = tuple(
        row.model_copy(update={"as_of": "latest"})
        if row.ref_id == "ref:risks"
        else row
        for row in packet.evidence
    )
    context, _output, raw = _stage2_materialization_fixture(
        packet=packet.model_copy(update={"evidence": evidence})
    )

    materialized = _materialize_v1(context, raw)

    assert materialized.candidates[0].driver_maturity[0].as_of == "2026-08-30"


def test_stage2_materializer_is_hash_stable() -> None:
    context, _output, raw = _stage2_materialization_fixture()

    first = _materialize_v1(context, raw)
    second = _materialize_v1(context, raw)

    assert canonical_sha256(first.model_dump(mode="json")) == canonical_sha256(
        second.model_dump(mode="json")
    )
    assert all(
        "as_of" not in row
        for candidate in raw["candidates"]
        for row in candidate["driver_maturity"]
    )


def test_stage2_materializer_rejects_model_authored_as_of() -> None:
    context, _output, raw = _stage2_materialization_fixture()
    raw["candidates"][0]["driver_maturity"][0]["as_of"] = "2026-08-30"

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_model_authored_as_of_forbidden",
    ):
        _materialize_v1(context, raw)


def test_stage2_materializer_rejects_symbolic_only_without_global_fallback() -> None:
    packet = _packet()
    evidence = tuple(
        row.model_copy(update={"as_of": "latest"})
        if row.ref_id in {"ref:valuation", "ref:risks"}
        else row
        for row in packet.evidence
    )
    context, _output, raw = _stage2_materialization_fixture(
        packet=packet.model_copy(update={"evidence": evidence})
    )

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_materialization_no_concrete_owned_date",
    ):
        _materialize_v1(context, raw)


def test_stage2_materializer_rejects_unknown_ref() -> None:
    context, _output, raw = _stage2_materialization_fixture()
    raw["candidates"][0]["driver_maturity"][0][
        "supporting_evidence_refs"
    ] = ["ref:not-owned"]

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_materialization_unknown_ticker_local_ref",
    ):
        _materialize_v1(context, raw)


def test_stage2_materializer_rejects_cross_ticker_ref() -> None:
    packet = _packet()
    other = packet.model_copy(
        update={
            "ticker": "OTHER",
            "company_name": "Other Company",
            "evidence": (
                packet.evidence[0].model_copy(
                    update={"ref_id": "other:owned", "as_of": "2026-08-30"}
                ),
            ),
            "evidence_sha256": "other-fixture",
        }
    )
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": "TEST"}, {"ticker": "OTHER"}],
        },
        claim_id="claim-stage2-cross-ticker",
        evidence_packets=(packet, other),
    )
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(_core(),),
        candidates=(_candidate(),),
    )
    raw = _model_facing_stage2_payload(output)
    raw["candidates"][0]["driver_maturity"][0][
        "supporting_evidence_refs"
    ] = ["other:owned"]

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_materialization_unknown_ticker_local_ref",
    ):
        _materialize_v1(context, raw, subjects=("TEST",))


def test_stage2_materializer_rejects_future_derived_date() -> None:
    packet = _packet()
    evidence = tuple(
        row.model_copy(update={"as_of": "2026-08-31"})
        if row.ref_id == "ref:risks"
        else row
        for row in packet.evidence
    )
    context, _output, raw = _stage2_materialization_fixture(
        packet=packet.model_copy(update={"evidence": evidence})
    )

    with pytest.raises(
        Stage2MaturityAsOfMaterializationError,
        match="stage2_materialization_future_derived_date",
    ):
        _materialize_v1(context, raw)


def test_stage2_hard_validator_rejects_post_materialization_tamper() -> None:
    context, _output, raw = _stage2_materialization_fixture()
    materialized = _materialize_v1(context, raw)
    candidate = materialized.candidates[0]
    row = candidate.driver_maturity[0].model_copy(update={"as_of": "2026-08-29"})
    tampered = candidate.model_copy(update={"driver_maturity": (row,)})

    validation = validate_accepted_v2_stage2_candidate(
        context.evidence_packets[0],
        tampered,
        materialized.fundamental_cores[0],
        context.evidence_ownership[0],
    )

    assert "maturity_evidence_date_not_owned:신규 제품 수익화" in validation.errors


def _candidate_with_balance(buy: float) -> PreconfirmationDecisionCandidate:
    balance = DirectionalBalance(buy=buy, sell=10 - buy)
    decision = decision_from_directional_balance(balance)
    baseline = _candidate()
    return _candidate_with_current_core_sha(baseline.model_copy(
        update={
            "decision": decision,
            "directional_balance": balance,
            "pre_confirmation_buy": decision == "BUY",
            "preconfirmation_buy_explanation": (
                baseline.preconfirmation_buy_explanation if decision == "BUY" else None
            ),
            "post_confirmation_hold": False,
            "postconfirmation_hold_explanation": None,
        }
    ))


@pytest.mark.parametrize(
    ("buy", "expected_decision", "expected_render"),
    (
        (6, "BUY", "BUY 6 : SELL 4"),
        (5, "HOLD", "BUY 5 : SELL 5"),
        (4, "SELL", "BUY 4 : SELL 6"),
        (5.5, "HOLD", "BUY 5.5 : SELL 4.5"),
    ),
)
def test_directional_balance_derives_required_label_anchors(
    buy: float,
    expected_decision: str,
    expected_render: str,
) -> None:
    candidate = _candidate_with_balance(buy)

    assert candidate.decision == expected_decision
    assert render_directional_balance(candidate.directional_balance) == expected_render
    assert validate_preconfirmation_candidate(_packet(), candidate).valid is True


@pytest.mark.parametrize(
    ("buy", "sell", "error"),
    (
        (6, 3, "directional_balance_sum_not_10"),
        (5.25, 4.75, "directional_balance_false_precision"),
        (float("nan"), 5, "directional_balance_non_finite"),
    ),
)
def test_directional_balance_rejects_invalid_sum_precision_and_non_finite_values(
    buy: float,
    sell: float,
    error: str,
) -> None:
    with pytest.raises(ValidationError, match=error):
        DirectionalBalance(buy=buy, sell=sell)


@pytest.mark.parametrize(
    ("field", "text", "expected_error"),
    (
        (
            "balance_summary",
            "BUY 확률은 높지만 위험도 남아 있습니다.",
            "directional_balance_probability_language",
        ),
        (
            "balance_summary",
            "고정 점수 합산으로 매수 우위를 정했습니다.",
            "directional_balance_fixed_score_language",
        ),
        (
            "buy_drivers",
            (_claim("ref:valuation", "매수 승률이 높습니다."),),
            "directional_balance_probability_language",
        ),
    ),
)
def test_directional_balance_rejects_probability_and_fixed_score_language(
    field: str,
    text: object,
    expected_error: str,
) -> None:
    candidate = _candidate().model_copy(update={field: text})

    assert expected_error in validate_preconfirmation_candidate(_packet(), candidate).errors


def test_directional_balance_rejects_unregistered_number_and_technical_only_ownership() -> None:
    numeric = _candidate().model_copy(
        update={"balance_summary": "매출 30%를 균형의 직접 근거로 사용했습니다."}
    )
    technical_only = _candidate().model_copy(
        update={
            "buy_drivers": (_claim("ref:price", "가격 구조가 매수 방향을 지지합니다."),),
            "sell_drivers": (_claim("ref:market", "시장 흐름이 매도 방향 근거입니다."),),
        }
    )

    assert "directional_balance_unregistered_numeric" in (
        validate_preconfirmation_candidate(_packet(), numeric).errors
    )
    assert "directional_balance_without_fundamental_or_valuation_driver" in (
        validate_preconfirmation_candidate(_packet(), technical_only).errors
    )


def test_preflight_repairs_batch_schema_before_candidate_validation(monkeypatch, tmp_path) -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-preflight-schema-repair",
        evidence_packets=(packet,),
    )
    candidate = _candidate()
    core = _core(candidate)
    core_batch = AcceptedV2FundamentalCoreBatch(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        cores=(core,),
    )
    valid = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(core,),
        candidates=(candidate,),
    )
    valid_raw = _model_facing_stage2_payload(valid)
    invalid = _model_facing_stage2_payload(valid)
    maturity = invalid["candidates"][0]["driver_maturity"][0]
    maturity["contradicting_claim_refs"].append(maturity["supporting_claim_refs"][0])

    def fake_invoke(**kwargs) -> None:
        output = kwargs["output"]
        if "core-batch" in output.name:
            payload = core_batch.model_dump(mode="json")
        else:
            payload = valid_raw if "schema-repair" in output.name else invalid
        output.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(preflight, "_signed_in_codex_bin", lambda: "codex")
    monkeypatch.setattr(preflight, "_invoke_signed_in_codex", fake_invoke)

    result = preflight._codex_batch(context, output_dir=tmp_path, timeout=30)

    assert [candidate.ticker for candidate in result.candidates] == ["TEST"]
    repair_prompt = (tmp_path / "batch-01.schema-repair.txt").read_text(encoding="utf-8")
    assert "maturity_atomic_claim_polarity_overlap" in repair_prompt


def test_preflight_rate_limit_resume_sends_only_exact_remaining_subset(
    monkeypatch, tmp_path
) -> None:
    messages = [
        {
            "ticker": ticker,
            "logical_identity": f"test:{ticker}",
            "rendered_sha256": f"sha-{ticker}",
            "text": ticker,
        }
        for ticker in ("A", "B", "C")
    ]
    (tmp_path / "production-payloads.json").write_text(
        json.dumps({"messages": messages}), encoding="utf-8"
    )
    initial_rows = [
        {
            "ticker": ticker,
            "logical_identity": f"test:{ticker}",
            "rendered_sha256": f"sha-{ticker}",
            "exact_payload_match": True,
        }
        for ticker in ("A", "B")
    ]
    (tmp_path / "test-sink-receipt.json").write_text(
        json.dumps(
            {
                "status": "failed",
                "safe_error": "http_status_429",
                "rows": initial_rows,
            }
        ),
        encoding="utf-8",
    )
    for market, tickers in (("kr", ("A",)), ("us", ("B", "C"))):
        market_dir = tmp_path / market
        market_dir.mkdir()
        (market_dir / "accepted-artifact.json").write_text(
            json.dumps(
                {
                    "packet_id": f"packet-{market}",
                    "selected_subjects": tickers,
                    "ready_count": len(tickers),
                    "not_ready_count": 0,
                    "message_quality": {"status": "PASS"},
                }
            ),
            encoding="utf-8",
        )

    sent: list[str] = []

    async def fake_deliver(remaining, **kwargs):
        sent.extend(str(row["ticker"]) for row in remaining)
        return {
            "rows": [
                {
                    "ticker": row["ticker"],
                    "logical_identity": row["logical_identity"],
                    "rendered_sha256": row["rendered_sha256"],
                    "exact_payload_match": True,
                }
                for row in remaining
            ]
        }

    monkeypatch.setattr(preflight, "load_env_values", lambda path: {"token": "safe"})
    monkeypatch.setattr(
        preflight,
        "audit_test_sink",
        lambda values: {
            "available": True,
            "selected_test_key_name": "TEST_CHAT",
            "test_sink_alias": "test",
            "production_sink_alias": "production",
        },
    )
    monkeypatch.setattr(preflight, "deliver_test_messages", fake_deliver)

    asyncio.run(
        preflight._resume_test_sink(
            argparse.Namespace(output_dir=tmp_path, env_file=tmp_path / ".env")
        )
    )

    final_receipt = json.loads(
        (tmp_path / "test-sink-final-receipt.json").read_text(encoding="utf-8")
    )
    assert sent == ["C"]
    assert final_receipt["status"] == "sent"
    assert final_receipt["sent_message_count"] == 3
    assert final_receipt["continuation_sent_count"] == 1
    assert final_receipt["duplicate_count"] == 0


def test_partial_maturity_can_be_medium_confidence_preconfirmation_buy() -> None:
    packet = _packet()
    candidate = _candidate()
    validation = validate_preconfirmation_candidate(packet, candidate)
    assert validation.valid is True
    assert candidate.confidence == "MEDIUM"
    assert candidate.overall_maturity.maturity == "PARTIAL"
    assert candidate.pre_confirmation_buy is True

    rendered = render_preconfirmation_shadow(packet, candidate)
    quality = preconfirmation_message_quality((rendered,))
    assert quality["status"] == "PASS"
    assert "완전 확인 전 판단" in rendered.text


def test_partial_buy_requires_preconfirmation_flag_and_explanation() -> None:
    candidate = _candidate().model_copy(
        update={
            "pre_confirmation_buy": False,
            "preconfirmation_buy_explanation": None,
        }
    )

    validation = validate_preconfirmation_candidate(_packet(), candidate)

    assert requires_preconfirmation_buy(candidate) is True
    assert validation.valid is False
    assert validation.errors == ("preconfirmation_buy_flag_missing",)


def test_confirmed_buy_does_not_require_preconfirmation_flag() -> None:
    baseline = _candidate()
    candidate = baseline.model_copy(
        update={
            "driver_maturity": (
                baseline.driver_maturity[0].model_copy(
                    update={"maturity": EvidenceMaturity.CONFIRMED}
                ),
            ),
            "overall_maturity": OverallMaturityAssessment(
                maturity=EvidenceMaturity.CONFIRMED,
                basis=_claim("ref:thesis", "핵심 사업 증거는 충분히 확인됐습니다."),
            ),
            "pre_confirmation_buy": False,
            "preconfirmation_buy_explanation": None,
        }
    )

    assert requires_preconfirmation_buy(candidate) is False
    assert validate_preconfirmation_candidate(_packet(), candidate).valid is True


def test_preconfirmation_buy_is_independent_from_wait_and_unfavorable_timing() -> None:
    candidate = _candidate().model_copy(
        update={
            "new_buyer_axis": NewBuyerDecisionAxis(
                stance="WAIT",
                reason=_claim(
                    "ref:price", "진입 가격 확인 전까지 신규 관찰자는 기다립니다."
                ),
            ),
            "timing": "UNFAVORABLE",
            "timing_basis": _claim(
                "ref:price", "단기 가격 구조는 신규 진입에 불리합니다."
            ),
        }
    )

    validation = validate_preconfirmation_candidate(_packet(), candidate)

    assert validation.valid is True
    assert candidate.decision == "BUY"
    assert candidate.pre_confirmation_buy is True
    assert candidate.new_buyer_axis.stance == "WAIT"
    assert candidate.holder_axis.stance == "HOLDABLE"
    assert candidate.timing == "UNFAVORABLE"


def test_non_buy_cannot_set_preconfirmation_buy() -> None:
    candidate = _candidate().model_copy(
        update={
            "decision": "HOLD",
            "directional_balance": DirectionalBalance(buy=5, sell=5),
        }
    )

    validation = validate_preconfirmation_candidate(_packet(), candidate)

    assert requires_preconfirmation_buy(candidate) is False
    assert "preconfirmation_buy_without_buy_decision" in validation.errors


def test_preconfirmation_explanation_shape_remains_hard_required() -> None:
    payload = _candidate().model_dump(mode="json")
    payload["preconfirmation_buy_explanation"] = None

    with pytest.raises(ValidationError, match="preconfirmation_explanation_flag_mismatch"):
        PreconfirmationDecisionCandidate.model_validate(payload)


def test_confirmed_business_can_be_postconfirmation_hold() -> None:
    candidate = _candidate().model_copy(
        update={
            "decision": "HOLD",
            "directional_balance": DirectionalBalance(buy=5, sell=5),
            "pre_confirmation_buy": False,
            "preconfirmation_buy_explanation": None,
            "post_confirmation_hold": True,
            "postconfirmation_hold_explanation": PostconfirmationHoldExplanation(
                business_proof=_claim("ref:earnings", "사업 증거는 충분히 확인됐습니다."),
                price_repricing=_claim(
                    "ref:valuation", "가격도 함께 재평가돼 상방 여유가 줄었습니다."
                ),
            ),
            "driver_maturity": (
                _candidate()
                .driver_maturity[0]
                .model_copy(update={"maturity": EvidenceMaturity.CONFIRMED}),
            ),
            "overall_maturity": OverallMaturityAssessment(
                maturity=EvidenceMaturity.CONFIRMED,
                basis=_claim("ref:earnings", "핵심 경제성은 반복 증거로 확인됐습니다."),
            ),
            "asymmetry": _candidate().asymmetry.model_copy(
                update={"asymmetry": Asymmetry.BALANCED}
            ),
        }
    )
    assert validate_preconfirmation_candidate(_packet(), candidate).valid is True


@pytest.mark.parametrize(
    "maturity",
    (EvidenceMaturity.MIXED, EvidenceMaturity.UNKNOWN),
)
def test_nonconfirmed_maturity_without_postconfirmation_hold_is_valid(
    maturity: EvidenceMaturity,
) -> None:
    candidate = _candidate().model_copy(
        update={
            "overall_maturity": OverallMaturityAssessment(
                maturity=maturity,
                basis=_claim("ref:thesis", "사업 성숙도는 아직 확정되지 않았습니다."),
            ),
            "post_confirmation_hold": False,
            "postconfirmation_hold_explanation": None,
        }
    )

    assert validate_preconfirmation_candidate(_packet(), candidate).valid is True


def test_hold_with_mixed_maturity_without_postconfirmation_hold_is_valid() -> None:
    candidate = _candidate_with_current_core_sha(
        _candidate().model_copy(
            update={
                "decision": "HOLD",
                "directional_balance": DirectionalBalance(buy=5, sell=5),
                "pre_confirmation_buy": False,
                "preconfirmation_buy_explanation": None,
                "overall_maturity": OverallMaturityAssessment(
                    maturity=EvidenceMaturity.MIXED,
                    basis=_claim("ref:thesis", "사업 증거는 확인과 불확실성이 섞여 있습니다."),
                ),
                "post_confirmation_hold": False,
                "postconfirmation_hold_explanation": None,
                "asymmetry": _candidate().asymmetry.model_copy(
                    update={"asymmetry": Asymmetry.BALANCED}
                ),
            }
        )
    )

    assert validate_preconfirmation_candidate(_packet(), candidate).valid is True


@pytest.mark.parametrize(
    "maturity",
    (EvidenceMaturity.MIXED, EvidenceMaturity.UNKNOWN),
)
def test_postconfirmation_hold_requires_confirmed_maturity(
    maturity: EvidenceMaturity,
) -> None:
    candidate = _candidate_with_current_core_sha(
        _candidate().model_copy(
            update={
                "decision": "HOLD",
                "directional_balance": DirectionalBalance(buy=5, sell=5),
                "pre_confirmation_buy": False,
                "preconfirmation_buy_explanation": None,
                "overall_maturity": OverallMaturityAssessment(
                    maturity=maturity,
                    basis=_claim("ref:thesis", "사업 성숙도는 아직 확정되지 않았습니다."),
                ),
                "post_confirmation_hold": True,
                "postconfirmation_hold_explanation": PostconfirmationHoldExplanation(
                    business_proof=_claim("ref:earnings", "사업 증거가 일부 확인됐습니다."),
                    price_repricing=_claim("ref:valuation", "가격 재평가 여부를 점검합니다."),
                ),
                "asymmetry": _candidate().asymmetry.model_copy(
                    update={"asymmetry": Asymmetry.BALANCED}
                ),
            }
        )
    )

    validation = validate_preconfirmation_candidate(_packet(), candidate)

    assert validation.valid is False
    assert "postconfirmation_hold_without_confirmed_maturity" in validation.errors


def test_factual_safety_block_cannot_be_priced_as_investment_uncertainty() -> None:
    candidate = _candidate().model_copy(update={"factual_safety_state": FactualSafetyState.BLOCKED})
    errors = validate_preconfirmation_candidate(_packet(), candidate).errors
    assert "preconfirmation_logic_bypasses_data_safety" in errors
    assert "blocked_safety_with_pricing_requirement" in errors
    assert "blocked_safety_with_asymmetry" in errors


def test_technical_evidence_cannot_own_asymmetry() -> None:
    technical = _candidate().asymmetry.model_copy(
        update={
            "basis": _claim("ref:price", "가격 구조만으로 비대칭을 판단했습니다."),
            "downside_permanence": _claim("ref:price", "가격 구조가 하방을 설명합니다."),
            "upside_not_priced": _claim("ref:market", "시장 흐름이 상방을 설명합니다."),
        }
    )
    candidate = _candidate().model_copy(update={"asymmetry": technical})
    assert (
        "technical_feature_owns_asymmetry"
        in validate_preconfirmation_candidate(_packet(), candidate).errors
    )


def test_target_price_fixed_score_and_order_language_are_rejected() -> None:
    candidate = _candidate().model_copy(
        update={
            "decisive_reason": _claim(
                "ref:valuation",
                "목표가를 고정 점수 합산으로 정했으니 시장가 매수 주문이 적절합니다.",
            )
        }
    )
    errors = validate_preconfirmation_candidate(_packet(), candidate).errors
    assert "invented_target_price_language" in errors
    assert "fixed_score_language" in errors
    assert "order_command_language" in errors


def _adjudication(
    *,
    recommendation: str,
    accepted_decision: str,
    candidate: PreconfirmationDecisionCandidate | None = None,
    v1_decision: str = "HOLD",
) -> AcceptedV2Adjudication:
    candidate = candidate or _candidate()
    keep_v2 = recommendation == "KEEP_V2"
    prior_balance = {
        "BUY": DirectionalBalance(buy=6, sell=4),
        "HOLD": DirectionalBalance(buy=5, sell=5),
        "SELL": DirectionalBalance(buy=4, sell=6),
    }[v1_decision]
    return AcceptedV2Adjudication(
        ticker="TEST",
        v1_decision=v1_decision,
        v2_decision=candidate.decision,
        accepted_decision=accepted_decision,
        recommendation=recommendation,
        v1_overrequired_confirmation="NO",
        v2_underweighted_execution_risk="YES",
        v1_ignored_confirmation_cost="NO",
        v2_overstated_favorable_asymmetry="YES",
        valuation_or_expectation_misuse="NEITHER",
        data_quality_comparison_safe=True,
        accepted_directional_balance=(candidate.directional_balance if keep_v2 else prior_balance),
        accepted_buy_drivers=(
            candidate.buy_drivers
            if keep_v2
            else (_claim("ref:valuation", "보수적 평가가 매수 근거입니다."),)
        ),
        accepted_sell_drivers=(
            candidate.sell_drivers
            if keep_v2
            else (_claim("ref:risks", "실행 위험이 매도 근거입니다."),)
        ),
        accepted_balance_summary=(
            candidate.balance_summary
            if keep_v2
            else "평가 매력과 실행 위험을 함께 반영한 최종 균형입니다."
        ),
        decisive_basis=_claim("ref:risks", "실행 위험이 남아 현재는 보유 판단이 더 적절합니다."),
        bounded_repair="NONE",
    )


@pytest.mark.parametrize("prior_decision", ("BUY", "SELL"))
def test_current_neutral_balance_is_hold_regardless_of_prior_decision(
    prior_decision: str,
) -> None:
    packet = _packet()
    candidate = _candidate_with_balance(5)
    adjudication = _adjudication(
        recommendation="KEEP_V2",
        accepted_decision="HOLD",
        candidate=candidate,
        v1_decision=prior_decision,
    )

    plan = resolve_accepted_v2_decision(
        packet,
        candidate,
        v1_decision=prior_decision,
        material_disagreement=True,
        adjudication=adjudication,
    )

    assert plan.status == AcceptedDecisionStatus.READY
    assert plan.accepted_decision == "HOLD"
    assert plan.accepted_directional_balance == DirectionalBalance(buy=5, sell=5)
    assert plan.accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V2
    assert validate_accepted_v2_decision(packet, plan).valid is True


def test_no_disagreement_accepts_candidate_as_single_authority() -> None:
    packet = _packet()
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate().model_copy(
            update={
                "decision": "HOLD",
                "directional_balance": DirectionalBalance(buy=5, sell=5),
                "pre_confirmation_buy": False,
                "preconfirmation_buy_explanation": None,
            }
        ),
        v1_decision="HOLD",
        material_disagreement=False,
        adjudication=None,
    )
    assert plan.status == AcceptedDecisionStatus.READY
    assert plan.accepted_decision == "HOLD"
    assert plan.accepted_source == AcceptedDecisionSource.CANDIDATE
    assert validate_accepted_v2_decision(packet, plan).valid is True


def test_keep_v1_replaces_candidate_and_suppresses_rejected_prebuy() -> None:
    packet = _packet()
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=_adjudication(recommendation="KEEP_V1", accepted_decision="HOLD"),
    )
    assert plan.status == AcceptedDecisionStatus.READY
    assert plan.candidate_decision == "BUY"
    assert plan.accepted_decision == "HOLD"
    assert plan.accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V1
    assert plan.accepted_preconfirmation_buy is False
    assert plan.accepted_asymmetry == "UNKNOWN"
    assert validate_accepted_v2_decision(packet, plan).valid is True


def test_keep_v2_preserves_candidate_decision_and_prebuy() -> None:
    packet = _packet()
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=_adjudication(recommendation="KEEP_V2", accepted_decision="BUY"),
    )
    assert plan.accepted_decision == "BUY"
    assert plan.accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V2
    assert plan.accepted_preconfirmation_buy is True
    assert validate_accepted_v2_decision(packet, plan).valid is True


def test_missing_material_adjudication_fails_closed_without_candidate_fallback() -> None:
    plan = resolve_accepted_v2_decision(
        _packet(),
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=None,
    )
    assert plan.status == AcceptedDecisionStatus.NOT_READY
    assert plan.accepted_decision is None
    assert plan.denial_reason == "material_disagreement_without_final_adjudication"


def test_accepted_resolution_is_idempotent() -> None:
    packet = _packet()
    adjudication = _adjudication(recommendation="KEEP_V1", accepted_decision="HOLD")
    first = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=adjudication,
    )
    second = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=adjudication,
    )
    assert first == second
    assert first.accepted_decision_id == second.accepted_decision_id
    assert first.accepted_evidence_fingerprint == second.accepted_evidence_fingerprint


def test_accepted_renderer_uses_keep_v1_hold_not_raw_candidate_buy() -> None:
    packet = _packet()
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=_adjudication(recommendation="KEEP_V1", accepted_decision="HOLD"),
    )
    rendered = render_accepted_v2_shadow(packet, plan)
    assert rendered.candidate_decision == "BUY"
    assert rendered.accepted_decision == "HOLD"
    assert "AI 수용 판단\n종합 방향: HOLD" in rendered.text
    assert "신규 관찰자:" in rendered.text
    assert "보유자:" in rendered.text
    assert "AI 수용 판단: BUY" not in rendered.text
    assert "완전 확인 전 BUY" not in rendered.text
    assert accepted_message_quality((rendered,))["status"] == "PASS"


def test_accepted_render_validator_rejects_candidate_label_leak() -> None:
    packet = _packet()
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=_adjudication(recommendation="KEEP_V1", accepted_decision="HOLD"),
    )
    rendered = render_accepted_v2_shadow(packet, plan)
    validation = validate_accepted_v2_render(
        plan,
        rendered_decision="BUY",
        text=rendered.text.replace("AI 수용 판단: HOLD", "AI 수용 판단: BUY"),
    )
    assert validation.valid is False
    assert "rendered_decision_not_accepted_decision" in validation.errors


def test_hold_change_condition_removes_impossible_hold_to_hold_downgrade() -> None:
    claim = _claim(
        "ref:risks",
        "갱신요율과 손해율이 함께 악화하면 보유 판단으로 낮추고, "
        "자본 훼손이 구조화되면 매도 판단으로 전환한다.",
    )
    normalized = normalize_decision_change_condition("HOLD", "DOWNGRADE", claim)
    assert "보유 판단으로 낮추" not in normalized.text
    assert "HOLD 확신을 낮추고" in normalized.text
    assert "매도 판단으로 전환" in normalized.text
    assert normalized.evidence_refs == claim.evidence_refs
    assert (
        decision_change_condition_errors(
            "HOLD",
            upgrade_text="사업 증거가 확인되면 매수 판단을 재검토한다.",
            downgrade_text=normalized.text,
        )
        == ()
    )


def test_047810_internal_downgrade_label_wording_is_removed() -> None:
    claim = _claim(
        "ref:risks",
        "추가 하향 라벨은 없으며, 수주 수익성이 약화되면 보유 근거를 재검토합니다.",
    )

    normalized = normalize_decision_change_condition("HOLD", "DOWNGRADE", claim)

    assert "하향 라벨" not in normalized.text
    assert normalized.text == "수주 수익성이 약화되면 보유 근거를 재검토합니다."
    assert normalized.evidence_refs == claim.evidence_refs


def test_googl_like_price_timing_evidence_cannot_enter_fundamental_core() -> None:
    packet = _packet().model_copy(update={"ticker": "GOOGL"})
    ownership = AcceptedV2EvidenceOwnership(
        ticker="GOOGL",
        core_ref_ids=tuple(
            row.ref_id
            for row in packet.evidence
            if row.category not in {EvidenceCategory.PRICE_STRUCTURE, EvidenceCategory.MARKET}
        ),
        timing_ref_ids=("ref:market", "ref:price"),
        expectation_valuation=interaction_from_packet(packet),
    )
    valid_core = _core().model_copy(update={"ticker": "GOOGL"})
    contaminated_core = valid_core.model_copy(
        update={
            "decisive_reason": _claim(
                "ref:price",
                "현재 가격 위치가 방향 판단의 결정적 근거입니다.",
            )
        }
    )

    core_errors = validate_accepted_v2_fundamental_core(contaminated_core, ownership)
    candidate = _candidate().model_copy(
        update={
            "ticker": "GOOGL",
            "decisive_reason": contaminated_core.decisive_reason,
            "fundamental_core_sha256": accepted_v2_fundamental_core_sha256(valid_core),
        }
    )
    candidate_errors = validate_accepted_v2_candidate_ownership(
        candidate,
        valid_core,
        ownership,
    )

    assert "price_timing_in_fundamental_core:ref:price" in core_errors
    assert "price_timing_stage_mutated_fundamental_core" in candidate_errors


def _stage2_ownership(
    packet: DecisionEvidencePacket,
    ticker: str = "TEST",
) -> AcceptedV2EvidenceOwnership:
    return AcceptedV2EvidenceOwnership(
        ticker=ticker,
        core_ref_ids=tuple(
            row.ref_id
            for row in packet.evidence
            if row.category not in {EvidenceCategory.PRICE_STRUCTURE, EvidenceCategory.MARKET}
        ),
        timing_ref_ids=tuple(
            row.ref_id
            for row in packet.evidence
            if row.category in {EvidenceCategory.PRICE_STRUCTURE, EvidenceCategory.MARKET}
        ),
        expectation_valuation=interaction_from_packet(packet),
    )


def test_stage2_field_ownership_inventory_covers_complete_candidate_schema() -> None:
    inventory = preconfirmation_stage2_field_ownership_inventory()
    manifest = accepted_v2_stage2_validation_scope_manifest()

    assert {row["field_path"].removeprefix("$.") for row in inventory} == set(
        PreconfirmationDecisionCandidate.model_fields
    )
    assert {
        row["field_path"]
        for row in inventory
        if row["owner_stage"] == "FUNDAMENTAL_CORE"
    } == {
        "$.ticker",
        "$.decision",
        "$.holder_axis",
        "$.directional_balance",
        "$.buy_drivers",
        "$.sell_drivers",
        "$.balance_summary",
        "$.confidence",
        "$.decisive_reason",
    }
    assert manifest["claim_language_scope_after_trust"] == "STAGE2_OWNED_FIELDS_ONLY"
    assert manifest["unsupported_metric_scope_after_trust"] == "STAGE2_OWNED_FIELDS_ONLY"
    assert manifest["fields"] == list(inventory)


def test_stage2_trusts_exact_copied_core_numeric_claim() -> None:
    packet = _packet()
    candidate = _candidate_with_current_core_sha(
        _candidate().model_copy(
            update={
                "decisive_reason": _claim(
                    "ref:valuation",
                    "검증된 선행 평가 6.5배는 방향 판단의 정식 근거입니다.",
                )
            }
        )
    )
    core = _core(candidate)

    standalone = validate_preconfirmation_candidate(packet, candidate)
    trusted_stage2 = validate_accepted_v2_stage2_candidate(
        packet, candidate, core, _stage2_ownership(packet)
    )

    assert "freeform_exact_numeric_claim" in standalone.errors
    assert trusted_stage2.valid is True


def test_stage2_owned_exact_numeric_claim_remains_hard_failure() -> None:
    packet = _packet()
    candidate = _candidate().model_copy(
        update={
            "why_not_buy": _claim(
                "ref:valuation",
                "검증 전에는 선행 평가 6.5배만으로 신규 진입을 결정하지 않습니다.",
            )
        }
    )

    validation = validate_accepted_v2_stage2_candidate(
        packet, candidate, _core(candidate), _stage2_ownership(packet)
    )

    assert validation.valid is False
    assert "freeform_exact_numeric_claim" in validation.errors


def test_mutated_numeric_frozen_core_fails_before_claim_scope_exemption() -> None:
    packet = _packet()
    original = _candidate()
    mutated = original.model_copy(
        update={
            "decisive_reason": _claim(
                "ref:valuation",
                "검증된 선행 평가 6.5배를 새 핵심 근거로 사용합니다.",
            )
        }
    )

    validation = validate_accepted_v2_stage2_candidate(
        packet, mutated, _core(original), _stage2_ownership(packet)
    )

    assert validation.valid is False
    assert "price_timing_stage_mutated_fundamental_core" in validation.errors


def test_stage2_owned_unknown_evidence_ref_remains_hard_failure() -> None:
    packet = _packet()
    candidate = _candidate().model_copy(
        update={
            "why_not_buy": _claim(
                "ref:stage2-missing",
                "검증되지 않은 근거로 신규 진입을 결정하지 않습니다.",
            )
        }
    )

    validation = validate_accepted_v2_stage2_candidate(
        packet, candidate, _core(candidate), _stage2_ownership(packet)
    )

    assert validation.valid is False
    assert "unknown_evidence_ref:ref:stage2-missing" in validation.errors


def test_mutated_frozen_core_unknown_ref_fails_before_claim_scope_exemption() -> None:
    packet = _packet()
    original = _candidate()
    mutated = original.model_copy(
        update={
            "decisive_reason": _claim(
                "ref:frozen-core-missing",
                "검증되지 않은 참조로 핵심 방향을 바꿉니다.",
            )
        }
    )

    validation = validate_accepted_v2_stage2_candidate(
        packet, mutated, _core(original), _stage2_ownership(packet)
    )

    assert validation.valid is False
    assert "price_timing_stage_mutated_fundamental_core" in validation.errors


def test_stage2_trusts_exact_copied_core_prospective_roic_condition() -> None:
    packet = _packet()
    prospective = _claim(
        "ref:risks",
        "AI 투자가 FCF와 ROIC의 구조적 악화로 이어지는지 확인해야 합니다.",
    )
    baseline = _candidate()
    maturity = baseline.driver_maturity[0].model_copy(
        update={
            "contradicting_claim_refs": (
                maturity_atomic_claim_ref(ticker="TEST", claim=prospective),
            ),
        }
    )
    candidate = baseline.model_copy(
        update={
            "sell_drivers": (prospective,),
            "holder_axis": HolderDecisionAxis(stance="HOLDABLE", reason=prospective),
            "driver_maturity": (maturity,),
        }
    )
    candidate = _candidate_with_current_core_sha(candidate)
    core = _core(candidate)

    assert "unsupported_metric_or_inference" in validate_preconfirmation_candidate(
        packet, candidate
    ).errors
    assert validate_preconfirmation_stage2_owned_semantics(packet, candidate).valid is True
    assert validate_accepted_v2_stage2_candidate(
        packet, candidate, core, _stage2_ownership(packet)
    ).valid is True


def test_stage2_owned_roic_remains_hard_failure() -> None:
    packet = _packet()
    candidate = _candidate().model_copy(
        update={
            "new_buyer_axis": NewBuyerDecisionAxis(
                stance="WAIT",
                reason=_claim(
                    "ref:thesis",
                    "ROIC 개선이 확인되면 신규 진입을 다시 검토합니다.",
                ),
            )
        }
    )
    core = _core(candidate)
    validation = validate_accepted_v2_stage2_candidate(
        packet, candidate, core, _stage2_ownership(packet)
    )

    assert validation.valid is False
    assert "unsupported_metric_or_inference" in validation.errors


def test_mutated_core_roic_fails_before_frozen_core_trust() -> None:
    packet = _packet()
    original = _candidate()
    core = _core(original)
    mutated = original.model_copy(
        update={
            "holder_axis": HolderDecisionAxis(
                stance="HOLDABLE",
                reason=_claim("ref:thesis", "ROIC 개선을 보유 근거로 새로 사용합니다."),
            )
        }
    )
    validation = validate_accepted_v2_stage2_candidate(
        packet, mutated, core, _stage2_ownership(packet)
    )

    assert validation.valid is False
    assert "price_timing_stage_mutated_fundamental_core" in validation.errors


def test_clean_stage2_candidate_regression_passes_scoped_validator() -> None:
    packet = _packet()
    candidate = _candidate()

    assert validate_accepted_v2_stage2_candidate(
        packet,
        candidate,
        _core(candidate),
        _stage2_ownership(packet),
    ).valid is True


def test_self_transition_validator_covers_buy_hold_and_sell() -> None:
    assert decision_change_condition_errors(
        "BUY",
        upgrade_text="근거가 늘면 매수 판단으로 상향한다.",
        downgrade_text="근거가 약해지면 보유 판단을 재검토한다.",
    ) == ("self_transition_wording:BUY:UPGRADE",)
    assert decision_change_condition_errors(
        "HOLD",
        upgrade_text="근거가 늘면 매수 판단을 재검토한다.",
        downgrade_text="근거가 약해지면 보유 판단으로 낮춘다.",
    ) == ("self_transition_wording:HOLD:DOWNGRADE",)
    assert decision_change_condition_errors(
        "SELL",
        upgrade_text="근거가 회복되면 보유 판단을 재검토한다.",
        downgrade_text="근거가 더 약해지면 매도 판단으로 낮춘다.",
    ) == ("self_transition_wording:SELL:DOWNGRADE",)


def test_production_renderer_consumes_only_ready_accepted_plan() -> None:
    packet = _packet()
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=_adjudication(recommendation="KEEP_V1", accepted_decision="HOLD"),
    )
    rendered = render_accepted_v2_production(packet, plan)
    assert "🧠 AI 분석 판단\n종합 방향: HOLD" in rendered.text
    assert "신규 관찰자:" in rendered.text
    assert "보유자:" in rendered.text
    assert "판단 균형: BUY 5 : SELL 5" in rendered.text
    assert "SHADOW" not in rendered.text
    assert "후보" not in rendered.text
    assert "AI 분석 판단: BUY" not in rendered.text
    assert "분석 분류이며 주문·자동매매·의무 매매 지시가 아닙니다" not in rendered.text
    assert rendered.validation.valid is True


@pytest.mark.parametrize("market", ("kr", "us"))
@pytest.mark.parametrize("decision", ("BUY", "HOLD", "SELL"))
def test_production_renderer_omits_common_disclaimer_for_every_decision(
    market: str,
    decision: str,
) -> None:
    packet = _packet().model_copy(update={"market": market})
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="BUY",
        material_disagreement=False,
        adjudication=None,
    ).model_copy(
        update={
            "candidate_decision": decision,
            "accepted_decision": decision,
            "accepted_directional_balance": DirectionalBalance(
                buy=6 if decision == "BUY" else 5 if decision == "HOLD" else 4,
                sell=4 if decision == "BUY" else 5 if decision == "HOLD" else 6,
            ),
            "accepted_asymmetry": Asymmetry.UNKNOWN,
            "accepted_preconfirmation_buy": False,
            "accepted_postconfirmation_hold": False,
            "accepted_confirmation_cost_basis": None,
            "accepted_upgrade_condition": _claim(
                "ref:thesis", "사업 근거가 달라지면 상향 가능성을 다시 점검한다."
            ),
            "accepted_downgrade_condition": _claim(
                "ref:risks", "위험 근거가 달라지면 하향 가능성을 다시 점검한다."
            ),
        }
    )

    rendered = render_accepted_v2_production(packet, plan)

    assert f"AI 분석 판단\n종합 방향: {decision}" in rendered.text
    assert "신규 관찰자:" in rendered.text
    assert "보유자:" in rendered.text
    assert "분석 분류이며 주문·자동매매·의무 매매 지시가 아닙니다" not in rendered.text
    assert rendered.validation.valid is True


def test_v2_production_output_resolves_ready_plan_for_complete_scope() -> None:
    packet = _packet()
    runtime_packet = {
        "packet_id": packet.packet_id,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "stocks": [{"ticker": packet.ticker}],
    }
    context = build_accepted_v2_production_context(
        packet=runtime_packet,
        claim_id="claim-v2",
        evidence_packets=(packet,),
    )
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(_core(),),
        candidates=(_candidate(),),
    )
    artifact = validate_accepted_v2_production_output(context, output)
    assert artifact.status == "PASS"
    assert artifact.ready_count == 1
    assert artifact.not_ready_count == 0
    assert artifact.accepted_plans[0].accepted_decision == "BUY"
    assert artifact.blocks[0].decision == "BUY"
    assert "SHADOW" not in artifact.blocks[0].text
    assert artifact.decision_consistency["status"] == "PASS"
    assert artifact.decision_consistency["raw_candidate_used_as_final"] == 0
    assert artifact.decision_consistency["daily_review_overrides_valid_v2_accepted"] == 0


def test_standalone_numeric_candidate_plan_remains_strict() -> None:
    packet = _packet()
    candidate = _candidate_with_frozen_core_numeric_claims()
    plan = resolve_accepted_v2_decision(
        packet,
        candidate,
        v1_decision=candidate.decision,
        material_disagreement=False,
        adjudication=None,
    )

    validation = validate_accepted_v2_decision(packet, plan)

    assert validation.valid is False
    assert "adjudication_introduced_unregistered_numeric" in validation.errors


def test_finalizer_gate_allows_only_exact_owned_numeric_balance_summary() -> None:
    packet = _packet()
    candidate = _candidate()
    candidate = _candidate_with_current_core_sha(
        candidate.model_copy(
            update={"balance_summary": "평가 12.4172배와 실행 위험을 함께 반영합니다."}
        )
    )
    core = _core(candidate)
    plan = resolve_accepted_v2_decision(
        packet,
        candidate,
        v1_decision=candidate.decision,
        material_disagreement=False,
        adjudication=None,
    )
    scope = AcceptedDecisionFrozenCoreNumericScope(
        ticker=core.ticker,
        fundamental_core_sha256=accepted_v2_fundamental_core_sha256(core),
        directional_balance=core.directional_balance,
        buy_drivers=core.buy_drivers,
        sell_drivers=core.sell_drivers,
        balance_summary=core.balance_summary,
    )

    assert validate_accepted_v2_decision(
        packet,
        plan,
        frozen_core_numeric_scope=scope,
    ).valid

    mutated = plan.model_copy(
        update={"accepted_balance_summary": "평가 12.4173배와 실행 위험을 함께 반영합니다."}
    )
    assert "adjudication_introduced_unregistered_numeric" in validate_accepted_v2_decision(
        packet,
        mutated,
        frozen_core_numeric_scope=scope,
    ).errors


def test_integrated_finalizer_allows_exact_frozen_core_numeric_claims() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-frozen-core-numeric",
        evidence_packets=(packet,),
    )
    candidate = _candidate_with_frozen_core_numeric_claims()
    frozen_core = _core(candidate)
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(frozen_core,),
        candidates=(candidate,),
    )

    artifact = validate_accepted_v2_production_output(
        context,
        output,
        trusted_fundamental_core_batch=_trusted_core_batch(context, frozen_core),
    )

    assert artifact.status == "PASS"
    assert artifact.accepted_plans[0].accepted_buy_drivers == frozen_core.buy_drivers
    assert artifact.accepted_plans[0].accepted_sell_drivers == frozen_core.sell_drivers
    assert artifact.accepted_plans[0].accepted_balance_summary == frozen_core.balance_summary


def test_numeric_frozen_core_artifact_round_trip(
    tmp_path: Path,
) -> None:
    packet = _packet()
    runtime_packet = {
        "packet_id": packet.packet_id,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "stocks": [{"ticker": packet.ticker}],
    }
    context = build_accepted_v2_production_context(
        packet=runtime_packet,
        claim_id="claim-v2-frozen-core-round-trip",
        evidence_packets=(packet,),
    )
    candidate = _candidate_with_frozen_core_numeric_claims()
    frozen_core = _core(candidate)
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(frozen_core,),
        candidates=(candidate,),
    )
    artifact = validate_accepted_v2_production_output(
        context,
        output,
        trusted_fundamental_core_batch=_trusted_core_batch(context, frozen_core),
    )
    path = tmp_path / "accepted-v2.json"
    path.write_text(
        json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False),
        encoding="utf-8",
    )

    loaded = load_accepted_v2_production_artifact(
        path,
        packet=runtime_packet,
        claim_id=context.claim_id,
        trusted_fundamental_core_batch=_trusted_core_batch(context, frozen_core),
    )

    assert loaded == artifact


def test_numeric_frozen_core_artifact_requires_independent_core(
    tmp_path: Path,
) -> None:
    packet = _packet()
    runtime_packet = {
        "packet_id": packet.packet_id,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "stocks": [{"ticker": packet.ticker}],
    }
    context = build_accepted_v2_production_context(
        packet=runtime_packet,
        claim_id="claim-v2-independent-core-required",
        evidence_packets=(packet,),
    )
    candidate = _candidate_with_frozen_core_numeric_claims()
    frozen_core = _core(candidate)
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(frozen_core,),
        candidates=(candidate,),
    )
    artifact = validate_accepted_v2_production_output(
        context,
        output,
        trusted_fundamental_core_batch=_trusted_core_batch(context, frozen_core),
    )
    path = tmp_path / "accepted-v2.json"
    path.write_text(
        json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="accepted_decision_invalid:adjudication_introduced_unregistered_numeric",
    ):
        load_accepted_v2_production_artifact(
            path,
            packet=runtime_packet,
            claim_id=context.claim_id,
        )


def test_artifact_reader_rejects_joint_numeric_mutation_against_independent_core(
    tmp_path: Path,
) -> None:
    packet = _packet()
    runtime_packet = {
        "packet_id": packet.packet_id,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "stocks": [{"ticker": packet.ticker}],
    }
    context = build_accepted_v2_production_context(
        packet=runtime_packet,
        claim_id="claim-v2-artifact-joint-mutation",
        evidence_packets=(packet,),
    )
    original_candidate = _candidate_with_frozen_core_numeric_claims()
    original_core = _core(original_candidate)
    mutated_buy = original_candidate.buy_drivers[0].model_copy(
        update={"text": "검증된 평가 12.4173배가 매수 방향을 지지합니다."}
    )
    mutated_maturity = original_candidate.driver_maturity[0].model_copy(
        update={
            "supporting_claim_refs": (
                maturity_atomic_claim_ref(ticker="TEST", claim=mutated_buy),
            )
        }
    )
    mutated_candidate = _candidate_with_current_core_sha(
        original_candidate.model_copy(
            update={
                "buy_drivers": (mutated_buy,),
                "driver_maturity": (mutated_maturity,),
            }
        )
    )
    mutated_core = _core(mutated_candidate)
    mutated_output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(mutated_core,),
        candidates=(mutated_candidate,),
    )
    self_consistent_artifact = validate_accepted_v2_production_output(
        context,
        mutated_output,
        trusted_fundamental_core_batch=_trusted_core_batch(context, mutated_core),
    )
    path = tmp_path / "jointly-mutated-accepted-v2.json"
    path.write_text(
        json.dumps(self_consistent_artifact.model_dump(mode="json"), ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="v2_production_artifact_trusted_fundamental_core_mismatch:TEST",
    ):
        load_accepted_v2_production_artifact(
            path,
            packet=runtime_packet,
            claim_id=context.claim_id,
            trusted_fundamental_core_batch=_trusted_core_batch(context, original_core),
        )


def test_artifact_reader_rejects_tampered_accepted_plan_after_materialization_bypass(
    tmp_path: Path,
) -> None:
    packet = _packet()
    runtime_packet = {
        "packet_id": packet.packet_id,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "stocks": [{"ticker": packet.ticker}],
    }
    context = build_accepted_v2_production_context(
        packet=runtime_packet,
        claim_id="claim-v2-plan-tamper",
        evidence_packets=(packet,),
    )
    candidate = _candidate_with_frozen_core_numeric_claims()
    frozen_core = _core(candidate)
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(frozen_core,),
        candidates=(candidate,),
    )
    artifact = validate_accepted_v2_production_output(
        context,
        output,
        trusted_fundamental_core_batch=_trusted_core_batch(context, frozen_core),
    )
    accepted_plan = artifact.accepted_plans[0]
    tampered_claim = accepted_plan.accepted_buy_drivers[0].model_copy(
        update={"text": "검증된 평가 12.4173배가 매수 방향을 지지합니다."}
    )
    tampered_plan = accepted_plan.model_copy(
        update={"accepted_buy_drivers": (tampered_claim,)}
    )
    tampered_artifact = artifact.model_copy(
        update={"accepted_plans": (tampered_plan,)}
    )
    path = tmp_path / "tampered-plan-accepted-v2.json"
    path.write_text(
        json.dumps(tampered_artifact.model_dump(mode="json"), ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="accepted_decision_invalid:adjudication_introduced_unregistered_numeric",
    ):
        load_accepted_v2_production_artifact(
            path,
            packet=runtime_packet,
            claim_id=context.claim_id,
            trusted_fundamental_core_batch=_trusted_core_batch(context, frozen_core),
        )


def test_artifact_reader_rejects_wrong_independent_core_batch_identity(
    tmp_path: Path,
) -> None:
    packet = _packet()
    runtime_packet = {
        "packet_id": packet.packet_id,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "stocks": [{"ticker": packet.ticker}],
    }
    context = build_accepted_v2_production_context(
        packet=runtime_packet,
        claim_id="claim-v2-reader-core-identity",
        evidence_packets=(packet,),
    )
    candidate = _candidate_with_frozen_core_numeric_claims()
    frozen_core = _core(candidate)
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(frozen_core,),
        candidates=(candidate,),
    )
    artifact = validate_accepted_v2_production_output(
        context,
        output,
        trusted_fundamental_core_batch=_trusted_core_batch(context, frozen_core),
    )
    path = tmp_path / "accepted-v2.json"
    path.write_text(
        json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False),
        encoding="utf-8",
    )
    wrong_batch = _trusted_core_batch(context, frozen_core).model_copy(
        update={"claim_id": "different-claim"}
    )

    with pytest.raises(
        ValueError,
        match=(
            "v2_production_artifact_trusted_fundamental_core_scope_mismatch:"
            "claim_id_mismatch"
        ),
    ):
        load_accepted_v2_production_artifact(
            path,
            packet=runtime_packet,
            claim_id=context.claim_id,
            trusted_fundamental_core_batch=wrong_batch,
        )


def test_artifact_contract_rejects_serialized_trust_permission(
    tmp_path: Path,
) -> None:
    packet = _packet()
    runtime_packet = {
        "packet_id": packet.packet_id,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "stocks": [{"ticker": packet.ticker}],
    }
    context = build_accepted_v2_production_context(
        packet=runtime_packet,
        claim_id="claim-v2-serialized-trust",
        evidence_packets=(packet,),
    )
    candidate = _candidate()
    core = _core(candidate)
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(core,),
        candidates=(candidate,),
    )
    artifact = validate_accepted_v2_production_output(context, output)
    payload = artifact.model_dump(mode="json")
    payload["trusted_fundamental_core_batch"] = _trusted_core_batch(
        context,
        core,
    ).model_dump(mode="json")
    path = tmp_path / "serialized-trust-accepted-v2.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValidationError, match="extra_forbidden"):
        load_accepted_v2_production_artifact(
            path,
            packet=runtime_packet,
            claim_id=context.claim_id,
            trusted_fundamental_core_batch=_trusted_core_batch(context, core),
        )


def test_runtime_validate_output_forwards_independent_core_to_reader(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    packet = _packet()
    runtime_packet = {
        "packet_id": packet.packet_id,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "stocks": [{"ticker": packet.ticker}],
    }
    claim_id = "claim-v2-job-independent-core"
    context = build_accepted_v2_production_context(
        packet=runtime_packet,
        claim_id=claim_id,
        evidence_packets=(packet,),
    )
    candidate = _candidate_with_frozen_core_numeric_claims()
    frozen_core = _core(candidate)
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(frozen_core,),
        candidates=(candidate,),
    )
    paths = {
        name: tmp_path / filename
        for name, filename in {
            "context": "context.json",
            "core_temp": "core.json",
            "temp": "output.json",
            "final": "artifact.json",
            "receipt": "receipt.json",
        }.items()
    }
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(runtime_packet), encoding="utf-8")
    paths["context"].write_text(context.model_dump_json(), encoding="utf-8")
    paths["core_temp"].write_text(
        _trusted_core_batch(context, frozen_core).model_dump_json(),
        encoding="utf-8",
    )
    paths["temp"].write_text(output.model_dump_json(), encoding="utf-8")
    claim = {
        "packet_id": context.packet_id,
        "claim_id": claim_id,
        "packet_path": str(packet_path),
    }
    monkeypatch.setattr(accepted_v2_runtime_job, "_claim", lambda *_: claim)
    monkeypatch.setattr(accepted_v2_runtime_job, "_paths", lambda *_: paths)
    monkeypatch.setattr(
        accepted_v2_runtime_job,
        "_generation_identity",
        lambda *_: {"generation_id": "fixture-generation"},
    )

    receipt = accepted_v2_runtime_job.validate_output(context.packet_id, claim_id)

    assert receipt["status"] == "PASS"
    assert paths["final"].exists()
    assert paths["receipt"].exists()


def test_runtime_validate_output_rejects_mutated_output_with_original_core_temp(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    packet = _packet()
    runtime_packet = {
        "packet_id": packet.packet_id,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "stocks": [{"ticker": packet.ticker}],
    }
    claim_id = "claim-v2-job-mutated-output"
    context = build_accepted_v2_production_context(
        packet=runtime_packet,
        claim_id=claim_id,
        evidence_packets=(packet,),
    )
    original_candidate = _candidate_with_frozen_core_numeric_claims()
    original_core = _core(original_candidate)
    mutated_buy = original_candidate.buy_drivers[0].model_copy(
        update={"text": "검증된 평가 12.4173배가 매수 방향을 지지합니다."}
    )
    mutated_candidate = _candidate_with_current_core_sha(
        original_candidate.model_copy(update={"buy_drivers": (mutated_buy,)})
    )
    mutated_output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(_core(mutated_candidate),),
        candidates=(mutated_candidate,),
    )
    paths = {
        name: tmp_path / filename
        for name, filename in {
            "context": "context.json",
            "core_temp": "core.json",
            "temp": "output.json",
            "final": "artifact.json",
            "receipt": "receipt.json",
        }.items()
    }
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(runtime_packet), encoding="utf-8")
    paths["context"].write_text(context.model_dump_json(), encoding="utf-8")
    paths["core_temp"].write_text(
        _trusted_core_batch(context, original_core).model_dump_json(),
        encoding="utf-8",
    )
    paths["temp"].write_text(mutated_output.model_dump_json(), encoding="utf-8")
    claim = {
        "packet_id": context.packet_id,
        "claim_id": claim_id,
        "packet_path": str(packet_path),
    }
    monkeypatch.setattr(accepted_v2_runtime_job, "_claim", lambda *_: claim)
    monkeypatch.setattr(accepted_v2_runtime_job, "_paths", lambda *_: paths)
    monkeypatch.setattr(
        accepted_v2_runtime_job,
        "_generation_identity",
        lambda *_: {"generation_id": "fixture-generation"},
    )

    with pytest.raises(
        ValueError,
        match="v2_production_trusted_fundamental_core_mismatch:TEST",
    ):
        accepted_v2_runtime_job.validate_output(context.packet_id, claim_id)

    assert not paths["final"].exists()
    assert not paths["receipt"].exists()


def test_integrated_finalizer_without_trusted_core_keeps_numeric_gate_strict() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-untrusted-core-numeric",
        evidence_packets=(packet,),
    )
    candidate = _candidate_with_frozen_core_numeric_claims()
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(_core(candidate),),
        candidates=(candidate,),
    )

    with pytest.raises(
        ValueError,
        match="v2_production_accepted_plan_invalid:TEST:"
        "adjudication_introduced_unregistered_numeric",
    ):
        validate_accepted_v2_production_output(context, output)


def test_integrated_finalizer_rejects_joint_core_candidate_numeric_mutation() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-mutated-core-numeric",
        evidence_packets=(packet,),
    )
    candidate = _candidate_with_frozen_core_numeric_claims()
    trusted_core = _core(candidate)
    mutated_buy = candidate.buy_drivers[0].model_copy(
        update={"text": candidate.buy_drivers[0].text.replace("12.4172", "12.4173")}
    )
    mutated_candidate = _candidate_with_current_core_sha(
        candidate.model_copy(update={"buy_drivers": (mutated_buy,)})
    )
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(_core(mutated_candidate),),
        candidates=(mutated_candidate,),
    )

    with pytest.raises(
        ValueError,
        match="v2_production_trusted_fundamental_core_mismatch:TEST",
    ):
        validate_accepted_v2_production_output(
            context,
            output,
            trusted_fundamental_core_batch=_trusted_core_batch(context, trusted_core),
        )


def test_integrated_finalizer_rejects_wrong_trusted_core_batch_identity() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-core-identity",
        evidence_packets=(packet,),
    )
    candidate = _candidate_with_frozen_core_numeric_claims()
    frozen_core = _core(candidate)
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(frozen_core,),
        candidates=(candidate,),
    )
    wrong_batch = _trusted_core_batch(context, frozen_core).model_copy(
        update={"claim_id": "different-claim"}
    )

    with pytest.raises(
        ValueError,
        match="v2_production_trusted_fundamental_core_scope_mismatch:claim_id_mismatch",
    ):
        validate_accepted_v2_production_output(
            context,
            output,
            trusted_fundamental_core_batch=wrong_batch,
        )


def test_integrated_finalizer_keeps_stage2_numeric_claim_strict() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-stage2-numeric",
        evidence_packets=(packet,),
    )
    candidate = _candidate_with_frozen_core_numeric_claims()
    frozen_core = _core(candidate)
    numeric_new_buyer = candidate.new_buyer_axis.model_copy(
        update={
            "reason": candidate.new_buyer_axis.reason.model_copy(
                update={"text": "현재 10달러 가격은 신규 진입과 양립합니다."}
            )
        }
    )
    mutated_candidate = candidate.model_copy(update={"new_buyer_axis": numeric_new_buyer})
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(frozen_core,),
        candidates=(mutated_candidate,),
    )

    with pytest.raises(ValueError, match="freeform_exact_numeric_claim"):
        validate_accepted_v2_production_output(
            context,
            output,
            trusted_fundamental_core_batch=_trusted_core_batch(context, frozen_core),
        )


def test_integrated_finalizer_keeps_adjudication_numeric_claims_strict() -> None:
    packet = _packet()
    candidate = _candidate_with_frozen_core_numeric_claims()
    frozen_core = _core(candidate)
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-adjudication-numeric",
        evidence_packets=(packet,),
    ).model_copy(
        update={
            "prior_accepted": (
                AcceptedV2ProductionBaseline(
                    ticker=packet.ticker,
                    market="us",
                    accepted_decision="HOLD",
                    evidence_sha256="prior-evidence",
                    accepted_decision_id="prior-id",
                    source="fixture",
                ),
            )
        }
    )
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(frozen_core,),
        candidates=(candidate,),
        adjudications=(
            _adjudication(
                recommendation="KEEP_V2",
                accepted_decision="BUY",
                candidate=candidate,
                v1_decision="HOLD",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="v2_production_accepted_plan_invalid:TEST:"
        "adjudication_introduced_unregistered_numeric",
    ):
        validate_accepted_v2_production_output(
            context,
            output,
            trusted_fundamental_core_batch=_trusted_core_batch(context, frozen_core),
        )


def test_changed_v2_candidate_without_adjudication_is_suppressed_not_visible() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2",
        evidence_packets=(packet,),
    ).model_copy(
        update={
            "prior_accepted": (
                AcceptedV2ProductionBaseline(
                    ticker="TEST",
                    market="us",
                    accepted_decision="HOLD",
                    evidence_sha256="prior-evidence",
                    accepted_decision_id="prior-accepted-id",
                    source="fixture",
                ),
            )
        }
    )
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(_core(),),
        candidates=(_candidate(),),
    )
    artifact = validate_accepted_v2_production_output(context, output)
    assert artifact.status == "PARTIAL_SAFE"
    assert artifact.ready_count == 0
    assert artifact.not_ready_count == 1
    assert artifact.blocks == ()
    assert artifact.accepted_plans[0].denial_reason == (
        "material_disagreement_without_final_adjudication"
    )


def _same_evidence_buy_balance_context() -> AcceptedV2ProductionContext:
    packet = _packet()
    return build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-balance",
        evidence_packets=(packet,),
    ).model_copy(
        update={
            "prior_accepted": (
                AcceptedV2ProductionBaseline(
                    ticker="TEST",
                    market="us",
                    accepted_decision="BUY",
                    accepted_directional_balance=DirectionalBalance(buy=6, sell=4),
                    evidence_sha256=packet.evidence_sha256,
                    accepted_decision_id="prior-accepted-id",
                    source="fixture",
                ),
            )
        }
    )


def test_same_evidence_material_balance_move_requires_adjudication() -> None:
    context = _same_evidence_buy_balance_context()
    candidate = _candidate_with_balance(8)
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(_core(candidate),),
        candidates=(candidate,),
    )

    artifact = validate_accepted_v2_production_output(context, output)

    assert artifact.status == "PARTIAL_SAFE"
    assert artifact.blocks == ()
    assert artifact.accepted_plans[0].denial_reason == (
        "material_disagreement_without_final_adjudication"
    )


def test_same_evidence_material_candidate_move_can_keep_prior_balance() -> None:
    context = _same_evidence_buy_balance_context()
    candidate = _candidate_with_balance(8)
    adjudication = _adjudication(
        recommendation="KEEP_V1",
        accepted_decision="BUY",
        candidate=candidate,
        v1_decision="BUY",
    )
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(_core(candidate),),
        candidates=(candidate,),
        adjudications=(adjudication,),
    )

    artifact = validate_accepted_v2_production_output(context, output)

    assert artifact.status == "PASS"
    assert artifact.accepted_plans[0].accepted_decision == "BUY"
    assert artifact.accepted_plans[0].accepted_directional_balance == DirectionalBalance(
        buy=6, sell=4
    )
    assert artifact.decision_consistency["unexplained_accepted_balance_drift"] == 0


def test_same_evidence_material_accepted_balance_drift_fails_closed() -> None:
    context = _same_evidence_buy_balance_context()
    candidate = _candidate_with_balance(8)
    adjudication = _adjudication(
        recommendation="KEEP_V2",
        accepted_decision="BUY",
        candidate=candidate,
        v1_decision="BUY",
    )
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(_core(candidate),),
        candidates=(candidate,),
        adjudications=(adjudication,),
    )

    with pytest.raises(
        ValueError,
        match="v2_production_same_evidence_unexplained_balance_drift:TEST",
    ):
        validate_accepted_v2_production_output(context, output)


def test_same_evidence_v2_decision_churn_fails_closed() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2",
        evidence_packets=(packet,),
    ).model_copy(
        update={
            "prior_accepted": (
                AcceptedV2ProductionBaseline(
                    ticker="TEST",
                    market="us",
                    accepted_decision="HOLD",
                    evidence_sha256=packet.evidence_sha256,
                    accepted_decision_id="prior-accepted-id",
                    source="fixture",
                ),
            )
        }
    )
    candidate = _candidate()
    output = AcceptedV2ProductionBatchOutput(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        fundamental_cores=(_core(candidate),),
        candidates=(candidate,),
        adjudications=(_adjudication(recommendation="KEEP_V2", accepted_decision="BUY"),),
    )
    try:
        validate_accepted_v2_production_output(context, output)
    except ValueError as exc:
        assert "same_evidence_unexplained_churn:TEST" in str(exc)
    else:
        raise AssertionError("same-evidence decision churn must fail closed")


def test_decision_consistency_records_valid_adjudicated_change() -> None:
    packet = _packet()
    baseline = AcceptedV2ProductionBaseline(
        ticker="TEST",
        market="us",
        accepted_decision="HOLD",
        evidence_sha256="prior-evidence",
        accepted_decision_id="prior-accepted-id",
        source="fixture",
    )
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=_adjudication(recommendation="KEEP_V2", accepted_decision="BUY"),
    )
    rendered = render_accepted_v2_production(packet, plan)
    audit = audit_accepted_decision_consistency(
        evidence_packets=(packet,),
        prior_accepted=(baseline,),
        accepted_plans=(plan,),
        blocks=(
            AcceptedV2ProductionBlock(
                ticker="TEST",
                decision="BUY",
                accepted_decision_id=str(plan.accepted_decision_id),
                buy_balance=plan.accepted_directional_balance.buy,
                sell_balance=plan.accepted_directional_balance.sell,
                text=rendered.text,
            ),
        ),
    )

    row = audit.diagnostics[0]
    assert audit.status == "PASS"
    assert row.prior_accepted == "HOLD"
    assert row.fresh_candidate == "BUY"
    assert row.fresh_accepted == "BUY"
    assert row.valid_adjudication is True
    assert row.material_evidence_delta == (MaterialEvidenceDelta.FINGERPRINT_CHANGED_UNCLASSIFIED)
    assert audit.unexplained_accepted_decision_drift == 0
