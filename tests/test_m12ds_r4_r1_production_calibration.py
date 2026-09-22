from copy import deepcopy

import pytest

from app.services.accepted_calibration_message_service import AcceptedCalibrationPlan, digest
from app.services.accepted_decision_v2_service import render_accepted_v2_production
from tests.test_accepted_decision_v2_runtime import _packet


def plan_for(packet):
    row = dict(overall_direction="BUY", directional_buy_score=6, confidence="MEDIUM",
        new_buyer="WAIT", holder="HOLDABLE", supporting_refs=["claim:one"], contradicting_refs=[],
        confidence_caution_refs=[], data_quality_refs=[], reevaluation_refs=[],
        holder_reason_evidence_refs=["claim:one"], new_buyer_risk_refs=[],
        overall_reason="Observed business momentum remains constructive.",
        new_buyer_reason="Wait for an independently grounded entry range.",
        holder_reason="The business basis is intact without an active adverse trigger.")
    lineage = {"claim:one": (packet.evidence[0].ref_id,)}
    receipt = dict(status="PASS", errors=[], ticker=packet.ticker, source_generation_id="source-one",
        execution_generation_id="exec-one", evidence_packet_sha256=digest(packet.model_dump(mode="json")),
        decision_sha256=digest(row), entries_sha256=digest({}), claim_lineage_sha256=digest(lineage))
    return AcceptedCalibrationPlan(ticker=packet.ticker, source_generation_id="source-one",
        execution_generation_id="exec-one", evidence_packet_sha256=receipt["evidence_packet_sha256"],
        decision=row, entries={}, claim_lineage=lineage, acceptance=receipt, acceptance_sha256=digest(receipt))


def test_existing_production_entrypoint_renders_exact_axes_without_synthetic_legacy_fields():
    packet = _packet()
    plan = plan_for(packet)
    output = render_accepted_v2_production(packet, plan)
    assert output.validation.valid
    for field in ("overall_reason", "new_buyer_reason", "holder_reason"):
        assert plan.decision[field] in output.text
    assert "신규 관찰자: 확인 대기" in output.text
    assert "보유자: 보유 유지 가능" in output.text
    assert "성숙도" not in output.text and "HOLDABLE" not in output.text
    assert "상향 재평가" not in output.text and "claim:one" not in output.text


@pytest.mark.parametrize("key", ["ticker", "source_generation_id", "execution_generation_id", "evidence_packet_sha256", "acceptance_sha256"])
def test_identity_drift_rejected(key):
    packet = _packet()
    with pytest.raises(ValueError, match="identity_or_validation"):
        render_accepted_v2_production(packet, plan_for(packet).model_copy(update={key: "changed"}))


def test_mutated_decision_is_not_accepted_by_old_receipt():
    packet = _packet()
    plan = plan_for(packet)
    row = deepcopy(plan.decision)
    row["overall_direction"] = "SELL"
    with pytest.raises(ValueError, match="identity_or_validation"):
        render_accepted_v2_production(packet, plan.model_copy(update={"decision": row}))


def test_source_packet_mismatch_rejected():
    packet = _packet()
    with pytest.raises(ValueError, match="identity_or_validation"):
        render_accepted_v2_production(packet.model_copy(update={"assessment_date": "2026-09-01"}), plan_for(packet))


def test_market_existing_entrypoint_uses_bound_current_result_without_legacy_portfolio():
    from app.services.accepted_calibration_message_service import AcceptedMarketCalibration
    from app.services.daily_digest_renderer import render_daily_digest
    context = {"session": {"latest_completed_regular_session_date": "2026-09-21"}}
    decision = dict(market="KR", regime="MIXED", confidence="MEDIUM", breadth_state="Breadth is mixed.",
        leadership="Leadership is selective.", flows_or_participation="Flow evidence is unavailable.",
        rates_or_macro_context="Macro context is limited.")
    receipt = dict(status="PASS", errors=[], market="kr", assessment_date="2026-09-22",
        source_context_sha256=digest(context), decision_sha256=digest(decision))
    plan = AcceptedMarketCalibration(market="kr", assessment_date="2026-09-22", source_context=context,
        decision=decision, acceptance=receipt, acceptance_sha256=digest(receipt))
    text = render_daily_digest(None, accepted_market=plan)
    assert "방향 혼재" in text and "2026-09-21" in text and "야간선물" not in text
    assert decision["leadership"] in text
    with pytest.raises(ValueError, match="binding_mismatch"):
        render_daily_digest(None, accepted_market=plan.model_copy(update={"assessment_date": "2026-09-23"}))


def test_numeric_capture_guard_reuses_production_provenance_validator():
    from scripts.m12ds_r4_r1_accepted_capture import numeric_audit
    assert not numeric_audit(["Business evidence remains positive."], {}, "TEST")
    assert numeric_audit(["Revenue rose 99%."], {}, "TEST")
