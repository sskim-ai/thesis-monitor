from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from app.services.working_capital_user_visible_preintegration_service import (
    ENABLE_GATE_VERSION,
    ENABLED_EVIDENCE_STATE,
    PREVIEW_EVIDENCE_STATE,
    EnablementGate,
    NaturalProofEvidence,
    NaturalProofState,
    PreviewRendering,
    WorkingCapitalMetricFamily,
    WorkingCapitalUserVisibleMode,
    build_enablement_gate,
    build_preview_context,
    metric_families_for_mode,
    natural_proof_from_receipt,
    preflight_enablement_mode,
    preview_parity_errors,
    render_preview,
    resolve_user_visible_mode,
    safe_select_user_visible_inventory,
    validate_preview,
)
from scripts.phase9_1e_preintegration_evidence import build_evidence


ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "docs/reports/20260821-phase9-1d-readiness.json"
CASH_FLOW_PREVIEW = ROOT / "docs/reports/20260821-phase9-0e-full-preview.json"


@pytest.fixture(scope="module")
def phase_91d() -> dict[str, object]:
    return json.loads(READINESS.read_text(encoding="utf-8"))


def _proof(
    family: WorkingCapitalMetricFamily,
    state: NaturalProofState = NaturalProofState.LIVE_PASS,
) -> NaturalProofEvidence:
    if state != NaturalProofState.LIVE_PASS:
        return NaturalProofEvidence(family, state)
    return NaturalProofEvidence(
        metric_family=family,
        state=state,
        packet_id="packet-natural",
        receipt_id="receipt-natural",
        fact_ids=("fact:1",),
        relation_ids=("relation:1",),
        pit_safe=True,
        semantic_safe=True,
        causal_safe=True,
        numeric_binding_safe=True,
        production_influence_count=0,
        evidence_ref="archive/receipt.json",
    )


def _gate(
    family: WorkingCapitalMetricFamily,
    state: NaturalProofState = NaturalProofState.NOT_OBSERVED,
    **kwargs,
) -> EnablementGate:
    return build_enablement_gate(family, _proof(family, state), **kwargs)


def _subject(phase_91d: dict[str, object], ticker: str) -> dict[str, object]:
    return next(item for item in phase_91d["subjects"] if item["ticker"] == ticker)


def test_feature_mode_missing_and_invalid_fail_closed(monkeypatch) -> None:
    from app.services import working_capital_user_visible_preintegration_service as service

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: type("Settings", (), {"working_capital_user_visible_mode": "OFF"})(),
    )

    assert resolve_user_visible_mode() == WorkingCapitalUserVisibleMode.OFF
    assert resolve_user_visible_mode("") == WorkingCapitalUserVisibleMode.OFF
    assert resolve_user_visible_mode("not-a-mode") == WorkingCapitalUserVisibleMode.OFF


def test_mode_metric_families_are_exact_and_narrow() -> None:
    combined = metric_families_for_mode(
        WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR
    )
    assert combined == (
        WorkingCapitalMetricFamily.INVENTORY,
        WorkingCapitalMetricFamily.EXACT_TRADE_AR,
    )
    assert metric_families_for_mode(WorkingCapitalUserVisibleMode.OFF) == ()


@pytest.mark.parametrize(
    ("requested", "family"),
    (
        (
            WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY,
            WorkingCapitalMetricFamily.INVENTORY,
        ),
        (
            WorkingCapitalUserVisibleMode.SELECTIVE_EXACT_TRADE_AR,
            WorkingCapitalMetricFamily.EXACT_TRADE_AR,
        ),
    ),
)
def test_not_observed_natural_proof_blocks_selective_modes(requested, family) -> None:
    gate = _gate(family)
    preflight = preflight_enablement_mode(requested, {family: gate})

    assert gate.contract == ENABLE_GATE_VERSION
    assert gate.eligible_for_enablement is False
    assert gate.blocking_reasons == ("natural_proof_not_observed",)
    assert preflight.accepted is False
    assert preflight.effective_mode == WorkingCapitalUserVisibleMode.OFF


def test_inventory_live_pass_can_enable_without_trade_ar() -> None:
    inventory = _gate(
        WorkingCapitalMetricFamily.INVENTORY,
        NaturalProofState.LIVE_PASS,
    )
    trade_ar = _gate(WorkingCapitalMetricFamily.EXACT_TRADE_AR)

    inventory_only = preflight_enablement_mode(
        WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY,
        {
            WorkingCapitalMetricFamily.INVENTORY: inventory,
            WorkingCapitalMetricFamily.EXACT_TRADE_AR: trade_ar,
        },
    )
    combined = preflight_enablement_mode(
        WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR,
        {
            WorkingCapitalMetricFamily.INVENTORY: inventory,
            WorkingCapitalMetricFamily.EXACT_TRADE_AR: trade_ar,
        },
    )

    assert inventory_only.accepted is True
    assert inventory_only.effective_mode == WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY
    assert combined.accepted is False
    assert combined.effective_mode == WorkingCapitalUserVisibleMode.OFF


def test_inventory_only_rollout_rejects_combined_even_when_both_proofs_pass() -> None:
    gates = {
        family: _gate(family, NaturalProofState.LIVE_PASS) for family in WorkingCapitalMetricFamily
    }

    result = preflight_enablement_mode(
        WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR,
        gates,
    )

    assert result.accepted is False
    assert result.effective_mode == WorkingCapitalUserVisibleMode.OFF
    assert result.blocking_reasons == ("inventory_only_rollout_policy",)


def test_natural_fail_and_open_p0_block_enablement() -> None:
    failed = _gate(
        WorkingCapitalMetricFamily.INVENTORY,
        NaturalProofState.LIVE_FAIL,
    )
    p0 = _gate(
        WorkingCapitalMetricFamily.EXACT_TRADE_AR,
        NaturalProofState.LIVE_PASS,
        open_p0=("wrong_semantic",),
    )

    assert failed.blocking_reasons == ("natural_proof_failed",)
    assert p0.eligible_for_enablement is False
    assert "open_p0" in p0.blocking_reasons


def test_receipt_proof_requires_packet_fact_pit_semantic_and_zero_influence() -> None:
    receipt = {
        "status": "COMPLETE_PASS",
        "packet_id": "natural-packet",
        "receipt_id": "natural-receipt",
        "selected_metric_families": {"INV": "inventory"},
        "selected_fact_ids": {"INV": ["fact:inv"]},
        "selected_relation_ids": {"INV": ["relation:inv"]},
        "numeric_binding": {"automatic": 1, "manual": 0, "rejected": 0, "unresolved": 0},
        "semantic_error_count": 0,
        "quality_error_count": 0,
        "production_influence_count": 0,
    }
    sidecar = {"subjects": {"INV": {"pit_state": "PASS", "freshness_state": "CURRENT_FORMAL"}}}

    proof = natural_proof_from_receipt(
        WorkingCapitalMetricFamily.INVENTORY,
        receipt,
        sidecar,
        evidence_ref="archive/canary-receipt.json",
    )
    tainted = natural_proof_from_receipt(
        WorkingCapitalMetricFamily.INVENTORY,
        {**receipt, "production_influence_count": 1},
        sidecar,
        evidence_ref="archive/canary-receipt.json",
    )

    assert proof.state == NaturalProofState.LIVE_PASS
    assert proof.verified_live_pass is True
    assert tainted.state == NaturalProofState.LIVE_FAIL


def test_preview_reuses_91d_inventory_and_exact_trade_ar_with_feature_off(
    phase_91d,
) -> None:
    mode = WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR
    cases = (
        ("005930", WorkingCapitalMetricFamily.INVENTORY, "exact_total_inventory"),
        (
            "010120",
            WorkingCapitalMetricFamily.EXACT_TRADE_AR,
            "exact_trade_accounts_receivable",
        ),
    )
    for ticker, family, scope in cases:
        context = build_preview_context(
            _subject(phase_91d, ticker),
            _gate(family),
            preview_target_mode=mode,
        )
        assert context is not None
        assert context.metric_family == family
        assert context.semantic_scope == scope
        assert context.evidence_state == PREVIEW_EVIDENCE_STATE
        assert context.preview_selected is True
        assert context.user_visible_enabled is False
        assert context.ai_enabled is False
        assert context.fallback_enabled is False


def test_broad_ar_ap_insurance_and_stale_controls_are_not_preview_selected(
    phase_91d,
) -> None:
    mode = WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR
    inventory_gate = _gate(WorkingCapitalMetricFamily.INVENTORY)

    for ticker in ("003690", "012450", "TSM", "RXRX"):
        context = build_preview_context(
            _subject(phase_91d, ticker),
            inventory_gate,
            preview_target_mode=mode,
        )
        assert context is None


def test_cash_flow_redundancy_only_suppresses_narrower_selection(phase_91d) -> None:
    subject = _subject(phase_91d, "MU")
    context = build_preview_context(
        subject,
        _gate(WorkingCapitalMetricFamily.INVENTORY),
        preview_target_mode=(WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR),
        cash_flow_context_id="cf-visible-existing",
        cash_flow_period_end="2026-05-28",
    )

    assert context is not None
    assert context.preview_selected is False
    assert context.suppression_reasons == (
        "cash_flow_higher_priority_no_incremental_unknown_resolution",
    )
    assert context.cash_flow_alignment_state == "COMPATIBLE_PERIOD_END"
    assert context.user_visible_enabled is False


def test_cash_flow_incompatible_period_is_not_combined_or_used_as_redundancy(
    phase_91d,
) -> None:
    context = build_preview_context(
        _subject(phase_91d, "000660"),
        _gate(WorkingCapitalMetricFamily.INVENTORY),
        preview_target_mode=(WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR),
        cash_flow_context_id="cf-visible-incompatible",
        cash_flow_period_end="2026-03-31",
    )

    assert context is not None
    assert context.preview_selected is True
    assert context.cash_flow_alignment_state == "INCOMPATIBLE_PERIOD"
    assert context.display_reason == "selected_current_formal_material_relation"


def test_feature_off_is_kill_switch_even_after_live_pass(phase_91d) -> None:
    family = WorkingCapitalMetricFamily.INVENTORY
    gate = _gate(family, NaturalProofState.LIVE_PASS)
    subject = _subject(phase_91d, "005930")
    preview = build_preview_context(
        subject,
        gate,
        preview_target_mode=WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY,
    )
    enabled = build_preview_context(
        subject,
        gate,
        preview_target_mode=WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY,
        feature_mode=WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY,
    )

    assert preview is not None and preview.user_visible_enabled is False
    assert enabled is not None and enabled.user_visible_enabled is True
    assert enabled.evidence_state == ENABLED_EVIDENCE_STATE
    assert validate_preview(enabled, render_preview(enabled, channel="fallback")) == ()


def test_ai_fallback_preview_parity_and_numeric_owner(phase_91d) -> None:
    context = build_preview_context(
        _subject(phase_91d, "086280"),
        _gate(WorkingCapitalMetricFamily.EXACT_TRADE_AR),
        preview_target_mode=(WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR),
    )
    assert context is not None
    ai = render_preview(context, channel="ai_preview")
    fallback = render_preview(context, channel="fallback_preview")

    assert preview_parity_errors(ai, fallback) == ()
    assert validate_preview(context, ai) == ()
    assert validate_preview(context, fallback) == ()
    assert ai.text is not None and ai.text.count(context.display_value) == 1
    assert ai.numeric_owner == "business_earnings"
    assert "거래 매출채권" in ai.text
    assert "앞섰습니다. " in ai.text


def test_semantic_validator_rejects_advanced_ratio_and_status_change(phase_91d) -> None:
    context = build_preview_context(
        _subject(phase_91d, "010120"),
        _gate(WorkingCapitalMetricFamily.EXACT_TRADE_AR),
        preview_target_mode=(WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR),
    )
    assert context is not None
    safe = render_preview(context, channel="ai_preview")
    unsafe = PreviewRendering(**{**safe.__dict__, "text": f"{safe.text} DSO 악화"})

    assert "unsupported_semantic_or_causal_claim" in validate_preview(context, unsafe)
    assert "working_capital_only_status_change" in validate_preview(
        context,
        safe,
        thesis_status_changed=True,
    )


def test_exact_unknown_resolution_does_not_broaden_scope(phase_91d) -> None:
    exact = build_preview_context(
        _subject(phase_91d, "010120"),
        _gate(WorkingCapitalMetricFamily.EXACT_TRADE_AR),
        preview_target_mode=(WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR),
    )

    assert exact is not None
    assert len(exact.resolved_unknowns) == 1
    assert "매출채권" in exact.resolved_unknowns[0]
    assert (
        build_preview_context(
            _subject(phase_91d, "012450"),
            _gate(WorkingCapitalMetricFamily.EXACT_TRADE_AR),
            preview_target_mode=(
                WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR
            ),
        )
        is None
    )


def test_actual_preview_selector_parity_and_feature_off_counts(phase_91d) -> None:
    cash_flow = json.loads(CASH_FLOW_PREVIEW.read_text(encoding="utf-8"))
    cash_flow_contexts = {
        item["ticker"]: {
            "context_id": item["context_id"],
            "period_end": item["primary_period"]["period_end"],
        }
        for item in cash_flow["subjects"]
        if item.get("context_id")
    }
    gates = {family: _gate(family) for family in WorkingCapitalMetricFamily}
    contexts = [
        context
        for subject in phase_91d["subjects"]
        if (family_value := subject.get("runtime_selected_metric"))
        if (
            context := build_preview_context(
                subject,
                gates[WorkingCapitalMetricFamily(family_value)],
                preview_target_mode=(
                    WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR
                ),
                cash_flow_context_id=(
                    cash_flow_contexts.get(subject["ticker"], {}).get("context_id")
                ),
                cash_flow_period_end=(
                    cash_flow_contexts.get(subject["ticker"], {}).get("period_end")
                ),
            )
        )
    ]

    assert len(contexts) == 7
    assert sum(item.preview_selected for item in contexts) == 5
    assert sum(item.metric_family == WorkingCapitalMetricFamily.INVENTORY for item in contexts) == 5
    assert (
        sum(item.metric_family == WorkingCapitalMetricFamily.EXACT_TRADE_AR for item in contexts)
        == 2
    )
    assert all(item.user_visible_enabled is False for item in contexts)
    assert all(item.feature_mode == WorkingCapitalUserVisibleMode.OFF for item in contexts)


def test_user_visible_service_is_imported_only_by_intended_production_paths() -> None:
    production_paths = (
        ROOT / "app/services/ai_review_service.py",
        ROOT / "app/services/notification_service.py",
        ROOT / "app/jobs/ai_review.py",
    )
    token = "working_capital_user_visible_preintegration_service"

    assert token in production_paths[0].read_text(encoding="utf-8")
    assert token in production_paths[1].read_text(encoding="utf-8")
    assert token not in production_paths[2].read_text(encoding="utf-8")


def test_runtime_inventory_selection_is_dynamic_and_trade_ar_stays_off(
    phase_91d,
) -> None:
    inventory_gate = _gate(
        WorkingCapitalMetricFamily.INVENTORY,
        NaturalProofState.LIVE_PASS,
    )
    trade_ar_gate = _gate(WorkingCapitalMetricFamily.EXACT_TRADE_AR)
    source = _subject(phase_91d, "005930")["context"]
    unknowns = tuple(
        item["original"]
        for item in source["resolved_unknowns"]
        if item.get("state") == "RESOLVED_EXACT"
    )
    gates = {
        WorkingCapitalMetricFamily.INVENTORY: inventory_gate,
        WorkingCapitalMetricFamily.EXACT_TRADE_AR: trade_ar_gate,
    }
    selected = safe_select_user_visible_inventory(
        ticker="005930",
        market="kr",
        packet_id="packet-runtime",
        assessment_date=date(2026, 8, 22),
        industry="memory_semiconductor",
        monitoring_text="메모리 ASP HBM 재고",
        existing_unknowns=unknowns,
        latest_formal_balance_date=date(2026, 6, 30),
        latest_provisional_period_end=None,
        cash_flow_context_id=None,
        cash_flow_period_end=None,
        rollout_mode="SELECTIVE_INVENTORY",
        gates=gates,
    )
    trade_ar_request = safe_select_user_visible_inventory(
        ticker="010120",
        market="kr",
        packet_id="packet-runtime",
        assessment_date=date(2026, 8, 22),
        industry="industrial_epc",
        monitoring_text="매출채권 회수",
        existing_unknowns=("거래 매출채권 추이를 확인하지 못했습니다.",),
        latest_formal_balance_date=date(2026, 6, 30),
        latest_provisional_period_end=None,
        cash_flow_context_id=None,
        cash_flow_period_end=None,
        rollout_mode="SELECTIVE_EXACT_TRADE_AR",
        gates=gates,
    )

    assert selected is not None
    assert selected.metric_family == WorkingCapitalMetricFamily.INVENTORY
    assert selected.semantic_scope == "exact_total_inventory"
    assert selected.user_visible_enabled is True
    assert trade_ar_request is None


def test_ai_fallback_parity_is_mandatory_in_enablement_gate() -> None:
    gate = _gate(
        WorkingCapitalMetricFamily.INVENTORY,
        NaturalProofState.LIVE_PASS,
        ai_fallback_parity_state="FAIL",
    )

    assert gate.eligible_for_enablement is False
    assert gate.blocking_reasons == ("ai_fallback_parity_not_passed",)


def test_runtime_inventory_does_not_stack_with_incompatible_cash_flow(
    phase_91d,
) -> None:
    gate = _gate(
        WorkingCapitalMetricFamily.INVENTORY,
        NaturalProofState.LIVE_PASS,
    )
    source = _subject(phase_91d, "000660")["context"]
    unknowns = tuple(
        item["original"]
        for item in source["resolved_unknowns"]
        if item.get("state") == "RESOLVED_EXACT"
    )

    selected = safe_select_user_visible_inventory(
        ticker="000660",
        market="kr",
        packet_id="packet-runtime",
        assessment_date=date(2026, 8, 22),
        industry="memory_semiconductor",
        monitoring_text="메모리 ASP HBM 재고",
        existing_unknowns=unknowns,
        latest_formal_balance_date=date(2026, 6, 30),
        latest_provisional_period_end=None,
        cash_flow_context_id="cf-visible-incompatible",
        cash_flow_period_end=date(2026, 3, 31),
        rollout_mode="SELECTIVE_INVENTORY",
        gates={WorkingCapitalMetricFamily.INVENTORY: gate},
    )

    assert selected is None


def test_archive_evidence_is_deterministic_and_ready() -> None:
    first = build_evidence()
    second = build_evidence()

    assert first == second
    assert first["selector"]["active_universe"] == 20
    assert first["selector"]["canary_candidates"] == 7
    assert first["selector"]["preview_selected"] == 5
    assert first["validation"]["numeric_binding"] == {
        "automatic": 5,
        "manual": 0,
        "rejected": 0,
        "unresolved": 0,
        "errors": [],
    }
    assert first["open_p0"] == []
    assert first["open_p1"] == []
    assert first["phase_9_1e_preintegration_ready"] is True
