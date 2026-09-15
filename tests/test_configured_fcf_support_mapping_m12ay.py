from __future__ import annotations

from app.services.configured_financial_support_concept_service import (
    CONTRACT_VERSION as FINANCIAL_SUPPORT_CONCEPT_CONTRACT,
    configured_financial_support_concepts,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.directional_financial_context_service import (
    FinancialClaimRole,
    financial_claim_role,
    financial_claim_row_requires_current_fcf_evidence,
    financial_claim_rows,
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    candidate_financial_framework_claims,
    financial_frameworks_in_text,
)
from app.services.logical_condition_service import CheckpointMetric


def _configured_ref(
    *,
    statement: str = "FCF 감소와 순부채 증가가 동반",
    metric_refs: tuple[CheckpointMetric, ...] = (CheckpointMetric.FCF,),
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id="configured:fcf",
        category=EvidenceCategory.RISKS,
        label="설정된 미래 논리 조건",
        statement=statement,
        source_ref="stock.thesis.weaken_signals",
        metric_refs=metric_refs,
    )


def _risk_candidate(text: str, ref: DecisionEvidenceRef) -> dict[str, object]:
    return {
        "risk_context": {
            "text": text,
            "evidence_refs": [ref.ref_id],
        }
    }


def _validation(text: str, ref: DecisionEvidenceRef):
    return validate_directional_financial_semantics(
        _risk_candidate(text, ref),
        supplied_refs=(ref,),
        allowed_ref_ids=(ref.ref_id,),
    )


def _fcf_row_requires_current(text: str, ref: DecisionEvidenceRef) -> bool:
    row = financial_claim_rows(_risk_candidate(text, ref))[0]
    return financial_claim_row_requires_current_fcf_evidence(
        row,
        evidence_by_ref={ref.ref_id: ref},
    )


def test_configured_financial_support_contract_is_frozen() -> None:
    assert FINANCIAL_SUPPORT_CONCEPT_CONTRACT == "configured-financial-support-concept-v1"


def test_structured_fcf_metric_maps_to_free_cash_flow_support() -> None:
    ref = _configured_ref()
    assert configured_financial_support_concepts(ref) == {
        "free_cash_flow",
        "net_debt",
    }


def test_explicit_fcf_text_fallback_is_bounded() -> None:
    english = _configured_ref(
        statement="free cash flow declines",
        metric_refs=(),
    )
    korean = _configured_ref(
        statement="잉여현금흐름 감소가 지속",
        metric_refs=(),
    )
    vague = _configured_ref(
        statement="현금창출력 약화",
        metric_refs=(),
    )

    assert configured_financial_support_concepts(english) == {"free_cash_flow"}
    assert configured_financial_support_concepts(korean) == {"free_cash_flow"}
    assert configured_financial_support_concepts(vague) == set()


def test_ocf_does_not_map_to_free_cash_flow_support() -> None:
    ref = _configured_ref(
        statement="영업현금흐름 감소",
        metric_refs=(CheckpointMetric.OCF,),
    )
    assert "free_cash_flow" not in configured_financial_support_concepts(ref)
    result = _validation("향후 FCF 감소 시 하향 재평가한다.", ref)
    assert not result.valid
    assert "unsupported_current_fcf_claim" in result.errors


def test_ocf_less_ppe_proxy_does_not_map_to_free_cash_flow_support() -> None:
    ref = _configured_ref(
        statement="OCF less PPE declines and is described as FCF",
        metric_refs=(
            CheckpointMetric.OCF,
            CheckpointMetric.PPE_CAPEX,
            CheckpointMetric.FCF,
        ),
    )
    assert "free_cash_flow" not in configured_financial_support_concepts(ref)
    result = _validation("향후 FCF 감소 시 하향 재평가한다.", ref)
    assert not result.valid
    assert "unsupported_current_fcf_claim" in result.errors


def test_nonconfigured_evidence_cannot_supply_configured_fcf_support() -> None:
    ref = DecisionEvidenceRef(
        ref_id="current:fcf",
        category=EvidenceCategory.EARNINGS,
        label="FCF",
        statement="FCF 감소",
        source_ref="stock.fact_catalog.free_cash_flow",
        metric_refs=(CheckpointMetric.FCF,),
    )
    assert configured_financial_support_concepts(ref) == set()


def test_future_fcf_condition_uses_configured_support() -> None:
    ref = _configured_ref()
    text = "향후 FCF 감소와 순부채 증가가 함께 확인되면 하향 재평가한다."
    candidate = _risk_candidate(text, ref)
    evidence_by_ref = {ref.ref_id: ref}
    net_debt_claims = tuple(
        claim
        for claim in candidate_financial_framework_claims(candidate)
        if claim.framework == "net_debt"
    )

    assert len(net_debt_claims) == 1
    assert financial_claim_role(
        net_debt_claims[0], evidence_by_ref=evidence_by_ref
    ) == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO
    assert not _fcf_row_requires_current(text, ref)
    result = _validation(text, ref)
    assert result.valid, result
    assert result.unsupported_current_fcf_claim_count == 0


def test_monitoring_obligation_and_english_parity_use_fcf_support() -> None:
    korean = _configured_ref(statement="FCF가 구조적으로 감소")
    english = _configured_ref(
        statement="free cash flow declines",
        metric_refs=(),
    )

    assert _validation("FCF 감소 여부를 감시해야 한다.", korean).valid
    assert _validation("monitor whether free cash flow declines.", english).valid


def test_configured_support_does_not_prove_current_fcf() -> None:
    ref = _configured_ref()
    for text in (
        "현재 FCF가 감소했다.",
        "FCF가 이미 악화됐다.",
        "현재 FCF는 음수다.",
        "FCF는 100이다.",
        "FCF 감소가 확인됐다.",
        "현재 FCF가 감소했고, 향후 추가 감소 시 논리를 하향 재평가한다.",
    ):
        result = _validation(text, ref)
        assert not result.valid, text
        assert "unsupported_current_fcf_claim" in result.errors, text


def test_general_framework_scanner_surface_does_not_expand_to_fcf() -> None:
    assert financial_frameworks_in_text("FCF 감소와 순부채 증가가 동반") == {
        "net_debt"
    }
    assert financial_frameworks_in_text("free cash flow declines") == set()
