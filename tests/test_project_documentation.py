import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (
    ROOT / "docs" / "MASTER_WORKFLOW.md",
    ROOT / "docs" / "PROJECT_HANDOFF.md",
    ROOT / "docs" / "NEXT_SESSION_PROMPT.md",
    ROOT / "docs" / "project-state.json",
    ROOT / "docs" / "reports" / "20260828-kr-market-internal-readiness.md",
    ROOT / "docs" / "reports" / "20260828-kr-market-internal-artifact-index.md",
    ROOT / "docs" / "reports" / "20260828-us-full-message-readiness.md",
    ROOT / "docs" / "reports" / "20260828-us-price-structure-preenable-readiness.md",
    ROOT / "docs" / "reports" / "20260828-us-macro-quality-readiness.md",
    ROOT / "docs" / "reports" / "20260829-us-morning-review-summary.md",
    ROOT / "docs" / "reports" / "20260829-us-morning-review-summary.json",
    ROOT / "docs" / "architecture" / "AI_ASSISTED_MONITORING.md",
    ROOT / "docs" / "architecture" / "OHLCV_STRUCTURE_ENGINE.md",
    ROOT / "docs" / "architecture" / "MARKET_INTELLIGENCE.md",
    ROOT / "docs" / "architecture" / "NUMERIC_PROVENANCE.md",
    ROOT / "docs" / "architecture" / "MONITORING_STATE_LIFECYCLE.md",
    ROOT / "docs" / "architecture" / "PEER_VALUATION.md",
    ROOT / "docs" / "architecture" / "NATURAL_LIVE_MESSAGE_HARDENING.md",
    ROOT / "docs" / "architecture" / "NIGHT_FUTURES_SESSION_BASIS.md",
    ROOT / "docs" / "architecture" / "NIGHT_FUTURES_PUBLICATION_TELEMETRY.md",
    ROOT / "docs" / "architecture" / "RUNTIME_REASONING_OWNERSHIP.md",
    ROOT / "docs" / "architecture" / "CASH_FLOW_CAPITAL_EFFICIENCY.md",
    ROOT / "docs" / "architecture" / "CASH_FLOW_SHADOW_CONSUMPTION.md",
    ROOT / "docs" / "architecture" / "CASH_FLOW_RUNTIME_SHADOW_CANARY.md",
    ROOT / "docs" / "architecture" / "CASH_FLOW_BASELINE_CONSISTENCY.md",
    ROOT / "docs" / "architecture" / "CASH_FLOW_USER_VISIBLE_INTEGRATION.md",
    ROOT / "docs" / "architecture" / "WORKING_CAPITAL_EVIDENCE.md",
    ROOT / "docs" / "architecture" / "WORKING_CAPITAL_SHADOW_CONSUMPTION.md",
    ROOT / "docs" / "architecture" / "WORKING_CAPITAL_RUNTIME_SHADOW_CANARY.md",
    ROOT / "docs" / "architecture" / "WORKING_CAPITAL_USER_VISIBLE_PREINTEGRATION.md",
    ROOT / "docs" / "architecture" / "KR_INVESTOR_FLOW_RECONCILIATION.md",
    ROOT / "docs" / "architecture" / "KR_PRODUCER_SESSION_AND_DELIVERY_INTEGRITY.md",
    ROOT / "docs" / "architecture" / "KR_PRODUCTION_PACKET_AND_SHADOW_GATE_SEPARATION.md",
    ROOT / "docs" / "architecture" / "MACRO_DIGEST_TEMPORAL_ELIGIBILITY.md",
    ROOT / "docs" / "architecture" / "COMMON_AI_CORE_V1.md",
    ROOT / "docs" / "architecture" / "MARKET_CONTEXT_ADAPTER.md",
    ROOT / "docs" / "architecture" / "KR_MARKET_CONTEXT_ADAPTER.md",
    ROOT / "docs" / "architecture" / "KIWOOM_KR_MARKET_CONTEXT.md",
    ROOT / "docs" / "architecture" / "KR_MARKET_FLOW_RECONCILIATION.md",
    ROOT / "docs" / "architecture" / "KR_MARKET_BREADTH.md",
    ROOT / "docs" / "architecture" / "US_MARKET_CONTEXT_ADAPTER.md",
    ROOT / "docs" / "architecture" / "MARKET_RESEARCH_SEED_ADAPTERS.md",
    ROOT / "docs" / "architecture" / "PRODUCTION_RESEARCH_CONNECTOR_BOUNDARY.md",
    ROOT / "docs" / "architecture" / "FREE_ANALYST_PRODUCTION_INTEGRATION.md",
    ROOT / "docs" / "architecture" / "ADAPTIVE_RENDERER_PRODUCTION.md",
    ROOT / "docs" / "architecture" / "FREE_ANALYST_CANARY_POLICY.md",
    ROOT / "docs" / "architecture" / "FREE_ANALYST_MESSAGE_QUALITY.md",
    ROOT / "docs" / "architecture" / "KR_MARKET_DIGEST_QUALITY.md",
    ROOT / "docs" / "architecture" / "KR_SIZE_SECTOR_MESSAGE_POLICY.md",
    ROOT / "docs" / "architecture" / "KR_PRICE_STRUCTURE_SELECTIVE_ROLLOUT.md",
    ROOT / "docs" / "architecture" / "KR_TEST_SINK_ROLLOUT_SAFETY.md",
    ROOT / "docs" / "architecture" / "AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE.md",
    ROOT / "docs" / "architecture" / "PRICE_STRUCTURE_SHADOW_POLICY.md",
    ROOT / "docs" / "architecture" / "VARIABLE_AI_SWING_ANCHOR_SELECTION.md",
    ROOT / "docs" / "architecture" / "PRICE_ONLY_AI_ANCHOR_PACKET.md",
    ROOT / "docs" / "architecture" / "AI_ANCHOR_STABILITY_POLICY.md",
    ROOT / "docs" / "architecture" / "FIBONACCI_SR_OWNERSHIP.md",
    ROOT / "docs" / "architecture" / "CANONICAL_SWING_STRUCTURE_CANDIDATE.md",
    ROOT / "docs" / "architecture" / "FIBONACCI_VALID_ABSTENTION.md",
    ROOT / "docs" / "architecture" / "AI_ANCHOR_CONSENSUS_POLICY.md",
    ROOT / "docs" / "architecture" / "PRICE_STRUCTURE_WAVE_FIB_V3.md",
    ROOT / "docs" / "architecture" / "OHLCV_LONG_HISTORY_CONTRACT.md",
    ROOT / "docs" / "architecture" / "PRIMARY_MONTHLY_WAVE_HYPOTHESIS.md",
    ROOT / "docs" / "architecture" / "WAVE_FIBONACCI_SOURCE_PROVENANCE.md",
    ROOT / "docs" / "architecture" / "MULTI_TIMEFRAME_SR_CONFLUENCE_V3.md",
    ROOT / "docs" / "architecture" / "TECHNICAL_ZONE_EVIDENCE_FAMILIES.md",
    ROOT / "docs" / "architecture" / "PRICE_STRUCTURE_V3_SHADOW_POLICY.md",
    ROOT / "docs" / "architecture" / "OHLCV_BAR_COMPLETION_CONTRACT.md",
    ROOT / "docs" / "architecture" / "OHLCV_1200_BACKFILL_CACHE.md",
    ROOT / "docs" / "architecture" / "WAVE_DEGREE_CURRENT_CYCLE.md",
    ROOT / "docs" / "architecture" / "PRICE_STRUCTURE_V3_AI_FEEDBACK_LOOP.md",
    ROOT / "docs" / "architecture" / "WAVE_HYPOTHESIS_EQUIVALENCE_CLASS.md",
    ROOT / "docs" / "architecture" / "FIB_FAMILY_ENDPOINT_DEPENDENCY.md",
    ROOT / "docs" / "architecture" / "FIB_FAMILY_CONSENSUS_POLICY.md",
    ROOT / "docs" / "architecture" / "PRICE_STRUCTURE_V3_AMBIGUITY_SET.md",
    ROOT / "docs" / "architecture" / "FAMILY_FILTERED_CONFLUENCE.md",
    ROOT / "docs" / "architecture" / "DETERMINISTIC_SR_BASE_LAYER.md",
    ROOT / "docs" / "architecture" / "SR_NEAREST_VS_MAJOR.md",
    ROOT / "docs" / "architecture" / "SR_PROXIMITY_RELEVANCE_GATE.md",
    ROOT / "docs" / "architecture" / "SR_TIMEFRAME_FALLBACK_PROVENANCE.md",
    ROOT / "docs" / "architecture" / "FIB_OPTIONAL_CONFLUENCE_POLICY.md",
    ROOT / "docs" / "architecture" / "CROSS_TIMEFRAME_SR_RELEVANCE.md",
    ROOT / "docs" / "architecture" / "PRICE_STRUCTURE_V3_RENDERER_OWNERSHIP.md",
    ROOT / "docs" / "architecture" / "PRICE_STRUCTURE_V3_VALIDATOR_OWNERSHIP.md",
    ROOT / "docs" / "architecture" / "FIB_CONFLUENCE_RENDER_EQUIVALENCE.md",
    ROOT / "docs" / "architecture" / "CURRENT_SR_VS_STORED_PRICE_RULES.md",
    ROOT / "docs" / "architecture" / "LEGACY_TECHNICAL_PROSE_SUPPRESSION.md",
    ROOT / "docs" / "architecture" / "US_MORNING_MESSAGE_LAYOUT.md",
    ROOT / "docs" / "architecture" / "US_MACRO_MESSAGE_RENDERING.md",
    ROOT / "docs" / "architecture" / "EXACT_PAYLOAD_MESSAGE_QUALITY_VALIDATION.md",
    ROOT / "docs" / "architecture" / "US_MARKET_DIGEST_EVIDENCE_OWNERSHIP.md",
    ROOT / "docs" / "architecture" / "KOREA_NIGHT_FUTURES_IN_US_MORNING.md",
    ROOT / "docs" / "architecture" / "US_FULL_MESSAGE_REFINEMENT_POLICY.md",
    ROOT / "docs" / "architecture" / "CROSS_MARKET_AI_DECISION_ENGINE.md",
    ROOT / "docs" / "architecture" / "OHLCV_MULTI_TIMEFRAME_FEATURE_ENGINE.md",
    ROOT / "docs" / "architecture" / "DECISION_EVIDENCE_PACKET.md",
    ROOT / "docs" / "architecture" / "DECISION_VALIDATOR_OWNERSHIP.md",
    ROOT / "docs" / "architecture" / "DECISION_SHADOW_AND_CANARY_ROLLOUT.md",
    ROOT / "docs" / "reports" / "20260829-decision-canary-readiness.json",
    ROOT / "docs" / "reports" / "20260829-decision-validation.md",
    ROOT / "docs" / "reports" / "20260829-decision-calibration-readiness.json",
    ROOT / "docs" / "reports" / "20260829-repaired-20-stock-decisions.json",
    ROOT / "docs" / "reports" / "20260829-decision-polarity-readiness.json",
    ROOT / "docs" / "operations" / "AI_ASSISTED_PILOT.md",
    ROOT / "docs" / "operations" / "CASH_FLOW_USER_VISIBLE_KILL_SWITCH.md",
    ROOT / "docs" / "operations" / "WORKING_CAPITAL_USER_VISIBLE_KILL_SWITCH.md",
    ROOT / "docs" / "knowledge" / "README.md",
)
INVESTMENT_SHA = "dc747fff856530e82477851cbd0bb16c5876770de514a9c02cfd5a26ac91c312"
CHART_SHA = "beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_persistent_handoff_artifacts_and_state_are_current() -> None:
    assert all(path.exists() for path in DOCUMENTS)
    state = json.loads((ROOT / "docs" / "project-state.json").read_text())

    assert state["repository"] == "sskim-ai/thesis-monitor"
    assert state["branch"] == "main"
    assert state["experimental_branch"] == (
        "codex/20260830-v2-adjudicated-decision-ownership-repair"
    )
    assert state["current_phase"] == (
        "v2_accepted_decision_ownership_closed_ready_with_observation"
    )
    assert state["last_completed_phase"] == (
        "20260830_v2_adjudicated_decision_ownership_repair"
    )
    assert state["next_default_phase"] == (
        "review_accepted_v2_messages_before_bounded_migration"
    )
    v2_implementation_commit = "c0c9139babb06ead11112aea072a67ef364a9b22"
    accepted_implementation_commit = "f55605189ee0179ab4af7030b94d79d706ed32a8"
    implementation_commit = "069f002437163bff1df7aa6e258918c1777d5dfa"
    kr_size_sector_implementation = "6a54db130e95e25969a5ca0a100648d4a12c3aa2"
    preenable_implementation = "7d2823c236c458cf76c77faae043c6288e46e65e"
    top3_implementation = "a7de99c2d1d1211615e0fcbf4bd3eadc06d957fb"
    price_structure_repair_implementation = "04fb7ad7646a55e03000134f50b3f402a6c49c87"
    daily_1200_implementation = "f957bea48e1bf8df23c6b8fe769812ade5663456"
    kr_integration_commit = "848eb80f6ce6504a9a855973b591ee0749167514"
    detector_implementation_commit = "3685aa991589ca0e7cc560104d4ebf8289e3f91d"
    preenablement_commit = "84f8f549bc8fa0338309a84b23b2738f2e357646"
    prior_price_structure_commit = "631e82f202b6f081866ef83c8b67b2138a8b51d8"
    prior_fibonacci_commit = "0dfef76bba606f018893d6e68e7beaf410aa7438"
    shadow_code_commit = "f28d4bb3b8eacebe7fb48a3ca7800094711793eb"
    assert state["deployed_code_commit"] == state["recorded_base_commit"]
    assert state["main_code_commit"] == accepted_implementation_commit
    assert state["operating_code_commit"] == accepted_implementation_commit
    canary = state["cross_market_decision_bounded_canary_20260829"]
    assert canary["status"] == "ENABLED_AWAITING_NATURAL_PROOF"
    assert canary["kr_subjects"] == ["003690", "000660"]
    assert canary["us_subjects"] == ["GOOGL", "RXRX"]
    assert canary["current_distribution"] == {"BUY": 0, "HOLD": 3, "SELL": 1}
    assert canary["preenable_test_sink"] == "PASS_6_OF_6_EXACT"
    assert canary["production_recipient_send"] == 0
    assert canary["unexplained_canary_decision_churn"] == 0
    assert canary["kr_natural_cycles"] == 0
    assert canary["us_natural_cycles"] == 0
    assert canary["expansion_recommendation"] == "HOLD"
    polarity = state["decision_evidence_polarity_renderer_p1_repair_20260829"]
    assert polarity["status"] == "REPAIRED_REARMED_AWAITING_NATURAL_PROOF"
    assert polarity["polarity_repair_changed_decision"] == 0
    assert polarity["preenable_test_sink"] == "PASS_6_OF_6_EXACT"
    assert polarity["production_recipient_send"] == 0
    assert polarity["kr_natural_cycles"] == 0
    assert polarity["us_natural_cycles"] == 0
    v2 = state["preconfirmation_asymmetry_decision_engine_v2_20260830"]
    assert v2["status"] == "CLOSED_SHADOW_READY_WITH_OBSERVATION"
    assert v2["instruction_commit"] == "46bdf4c"
    assert v2["implementation_commit"] == v2_implementation_commit
    assert v2["reasoning_effort"] == "xhigh"
    assert v2["label_blind_shadow"] == "PASS_20_OF_20"
    assert v2["v2_distribution"] == {"BUY": 2, "HOLD": 14, "SELL": 4}
    assert v2["preconfirmation_buy_subjects"] == ["003690", "GOOGL"]
    assert v2["material_disagreements"] == 5
    assert v2["adjudications"] == 5
    assert v2["historical_replay_lookahead_leak"] == 0
    assert v2["test_sink_delivery"] == "PASS_20_OF_20_EXACT"
    assert v2["test_sink_duplicate"] == 0
    assert v2["test_sink_orphan"] == 0
    assert v2["production_recipient_send"] == 0
    assert v2["production_delivery_intent_created"] == 0
    assert v2["production_v2_exposure"] == 0
    assert v2["current_v1_state"] == "CANARY_UNCHANGED"
    assert v2["open_p0"] == []
    assert v2["open_material_p1"] == []
    assert v2["migration_recommendation"] == "READY_WITH_OBSERVATION"
    assert v2["next_action"] == "REVIEW_V2_SHADOW_DECISIONS"
    accepted = state["v2_adjudicated_decision_ownership_repair_20260830"]
    assert accepted["status"] == "CLOSED_READY_FOR_MIGRATION_REVIEW"
    assert accepted["instruction_commit"] == "4662c08"
    assert accepted["base_commit"] == "29bdd4cf378438fedad7f602b4b8ede80c46dd44"
    assert accepted["track_a_commit"] == (
        "5730f816617263c7b09d5683d3832c303d8f79ce"
    )
    assert accepted["track_b_commit"] == (
        "6370d3fa87c37f5616e1726c055f1bc5fb883f3d"
    )
    assert accepted["track_c_commit"] == accepted_implementation_commit
    assert accepted["candidate_distribution"] == {"BUY": 2, "HOLD": 14, "SELL": 4}
    assert accepted["accepted_distribution"] == {"BUY": 1, "HOLD": 16, "SELL": 3}
    assert accepted["accepted_preconfirmation_buy_subjects"] == ["GOOGL"]
    assert accepted["test_sink_delivery"] == "PASS_20_OF_20_EXACT"
    assert accepted["production_recipient_send"] == 0
    assert accepted["production_delivery_intent_created"] == 0
    assert accepted["production_v2_exposure"] == 0
    assert accepted["current_v1_state"] == "CANARY_UNCHANGED"
    assert accepted["open_p0"] == []
    assert accepted["open_material_p1"] == []
    assert accepted["migration_recommendation"] == "READY_WITH_OBSERVATION"
    assert accepted["next_action"] == "REVIEW_ACCEPTED_V2_MESSAGES"
    phase_8552 = state["phase_8_5_5_2_kr_structured_field_repetition"]
    assert phase_8552["status"] == "operating_shadow_pending_natural_proof"
    assert phase_8552["operating_shadow_promoted"] is True
    assert phase_8552["operating_smoke"] == "497_passed"
    assert state["persistent_gaps"]["current_price_rr_packet_numeric_path"] == "LIVE_PATH_PASS"
    assert state["persistent_gaps"]["natural_live_validation"] == "PARTIAL"
    assert state["persistent_gaps"]["reasoning_ownership"] == ("LIVE_PASS_RUN29")
    assert state["contracts"]["runtime_specificity"] == ("runtime-message-specificity-v2")
    assert state["contracts"]["runtime_reasoning_ownership"] == ("runtime-reasoning-ownership-v1")
    assert state["contracts"]["numeric_summary_ownership"] == ("numeric-summary-ownership-v1")
    assert state["contracts"]["typed_template_skeleton"] == ("typed-template-skeleton-v1")
    assert state["contracts"]["canonical_supply_flow_tuple"] == ("canonical-supply-flow-tuple-v1")
    assert state["contracts"]["v2_accepted_decision_ownership"] == (
        "v2-accepted-decision-ownership-v1"
    )
    assert state["contracts"]["v2_accepted_decision_renderer"] == (
        "v2-accepted-decision-shadow-renderer-v1"
    )
    assert state["contracts"]["v2_accepted_decision_migration_readiness"] == (
        "v2-accepted-decision-migration-readiness-v1"
    )
    assert state["contracts"]["deterministic_sr_base_layer"] == ("deterministic-sr-base-layer-v1")
    assert state["contracts"]["sr_proximity_relevance_gate"] == ("sr-proximity-relevance-gate-v1")
    assert state["contracts"]["major_sr_price_anchor_reality_gate"] == (
        "major-sr-price-anchor-reality-gate-v1"
    )
    assert state["contracts"]["price_structure_v3_current_data_shadow_validation"] == (
        "price-structure-v3-current-data-shadow-validation-v1"
    )
    assert state["contracts"]["price_structure_v3_renderer_ownership"] == (
        "price-structure-v3-renderer-ownership-v1"
    )
    assert state["contracts"]["price_structure_v3_validator_ownership"] == (
        "price-structure-v3-validator-ownership-v1"
    )
    convergence = state["run44_v3_validator_convergence"]
    assert convergence["status"] == "live_pass"
    assert convergence["latest_runtime_already_fixed"] is True
    assert convergence["runtime_hotfix_required"] is False
    assert convergence["run44_frozen_replay"] == "PASS"
    assert convergence["fallback_dynamic_resistance_not_rendered"] == 0
    assert convergence["selected_fact_missing_negative_control"] == ("FAIL_AS_EXPECTED")
    assert convergence["kr7_replay"] == "PASS_7_OF_7"
    assert convergence["us_replay"] == "PASS_13_OF_13"
    assert convergence["test_exact_payload_match"] == "PASS_22_OF_22"
    assert convergence["production_recipient_send"] == 0
    assert convergence["production_delivery_intent_created"] == 0
    assert convergence["natural_kr_close_v3_validator"] == (
        "LIVE_PASS_OPERATOR_AUTHORIZED_ONE_SHOT"
    )
    live_proof = state["run_now_one_shot_kr_close_live_proof"]
    assert live_proof["status"] == "LIVE_PASS"
    assert live_proof["implementation_commit"] == ("239db58958b1193a8fd591500618ee4e7940c994")
    assert live_proof["one_shot_run_count"] == 1
    assert live_proof["normal_recurring_schedule_changed"] == 0
    assert live_proof["residual_one_shot_schedule_count"] == 0
    assert live_proof["market_message"] == "PASS_1_OF_1"
    assert live_proof["stock_messages"] == "PASS_7_OF_7"
    assert live_proof["exact_payload_match"] == "PASS_8_OF_8"
    assert live_proof["duplicate"] == 0
    assert live_proof["orphan"] == 0
    assert live_proof["unowned_retry"] == 0
    assert live_proof["final_v3_validator_convergence"] == "LIVE_PASS"
    morning_review = state["us_morning_market_data_review_20260829"]
    assert morning_review["status"] == "PARTIAL_SAFE"
    assert morning_review["latest_completed_us_session"] == "2026-08-28"
    assert morning_review["core_etf_current"] == "PASS_5_OF_5"
    assert morning_review["sector_current"] == "PASS_11_OF_11"
    assert morning_review["nasdaq_breadth"] == "PUBLICATION_PENDING"
    assert morning_review["night_futures"] == "NOT_READY_SAFE_OMISSION"
    assert morning_review["natural_market_message_evidence_parity"] == "PASS"
    assert morning_review["natural_delivery"] == "PASS_14_OF_14"
    assert morning_review["rejected_ai_sent"] is False
    assert morning_review["open_p0"] == []
    assert morning_review["open_material_p1"] == ["run45_ai_full_stock_validation_rejected"]
    assert morning_review["runtime_behavior_changed"] is False
    repair = state["us_night_futures_friday_saturday_ai_validator_repair_20260829"]
    assert repair["status"] == "DEPLOYED_AWAITING_NATURAL_PROOF"
    assert repair["instruction_commit"] == ("f8ca4fcb4557037468e35578a98a66aa9cb750b5")
    assert repair["implementation_commit"] == ("f621b0ab253a3e9fc6752f7d7aff9ccdad06ca19")
    assert repair["implementation_github_actions_run"] == 33224154203
    assert repair["implementation_github_actions_status"] == ("passed_test_and_lint")
    assert repair["evidence_github_actions_run"] == 33224913606
    assert repair["evidence_github_actions_status"] == "passed_test_and_lint"
    assert repair["operating_promotion"] == "PASS"
    assert repair["api_health"] == "PASS"
    assert repair["post_deploy_smoke"] == "PASS_9_OF_9"
    assert repair["night_futures_source_date_semantics"] == "END_DATE"
    assert repair["friday_saturday_source_result"] == "UPSTREAM_NOT_PUBLISHED"
    assert repair["night_futures_outcome"] == "SOURCE_LIMITATION_SAFE"
    assert repair["primary_validator_before_after"] == [37, 0]
    assert repair["backup_validator_before_after"] == [4, 0]
    assert repair["runtime_message_quality"] == "PASS"
    assert repair["us13_ai_validation"] == "PASS"
    assert repair["test_sink_delivery"] == "PASS_14_OF_14"
    assert repair["test_sink_exact_payload_match"] is True
    assert repair["production_recipient_send"] == 0
    assert repair["production_delivery_intent_created"] == 0
    assert repair["open_p0"] == []
    assert repair["open_material_p1"] == []
    assert repair["next_action"] == "WAIT_FOR_NEXT_NATURAL_US_RUN"
    decision_engine = state["cross_market_ai_decision_engine_v1_20260829"]
    assert decision_engine["status"] == "TEST_SINK_READY"
    assert decision_engine["implementation_commit"] == shadow_code_commit
    assert decision_engine["reasoning_effort"] == "xhigh"
    assert decision_engine["current_shadow"] == "PASS_20_OF_20"
    assert decision_engine["numeric_binding"] == "PASS_54_OF_54_AUTOMATIC"
    assert decision_engine["temporal_shadow"] == "PARTIAL_SAFE_200_OF_200"
    assert decision_engine["historical_replay_lookahead_leak"] == 0
    assert decision_engine["unexplained_decision_churn"] == 0
    assert decision_engine["test_sink_delivery"] == "PASS_20_OF_20"
    assert decision_engine["production_recipient_send"] == 0
    assert decision_engine["production_delivery_intent_created"] == 0
    assert decision_engine["decision_canary_readiness"] == "PASS"
    assert decision_engine["production_canary_enabled"] is False
    assert decision_engine["open_p0"] == []
    assert decision_engine["open_material_p1"] == []
    quality_review = state["cross_market_ai_decision_quality_review_before_canary_20260829"]
    assert quality_review["status"] == "NOT_READY"
    assert quality_review["review_commit"] == ("cd829ff8009759af7f5c73e487e43c06dc4b1a9c")
    assert quality_review["reasoning_effort"] == "xhigh"
    assert quality_review["independent_review_label_blind"] == "PASS"
    assert quality_review["independent_review"] == "PASS_20_OF_20"
    assert quality_review["material_disagreement_count"] == 5
    assert quality_review["adjudication_count"] == 5
    assert quality_review["final_review_distribution"] == {
        "BUY": 2,
        "HOLD": 15,
        "SELL": 3,
    }
    assert quality_review["hold_default_bias"] == "MATERIAL"
    assert quality_review["sell_suppression_bias"] == "MATERIAL"
    assert quality_review["cross_market_decision_semantics"] == "PASS"
    assert quality_review["production_canary_enabled"] is False
    assert quality_review["production_decision_message_sent"] == 0
    assert quality_review["open_p0"] == []
    assert len(quality_review["open_material_p1"]) == 4
    calibration = state["decision_calibration_p1_repair_before_canary_20260829"]
    assert calibration["status"] == "READY_WITH_OBSERVATION"
    assert calibration["implementation_commit"] == ("930952132077e8403bcec1a7e2c52d5732d8521a")
    assert calibration["reasoning_effort"] == "xhigh"
    assert calibration["same_evidence_blind_rerun"] == "PASS_20_OF_20"
    assert calibration["bounded_adjudication"] == "PASS_9_OF_9"
    assert calibration["repaired_distribution"] == {
        "BUY": 0,
        "HOLD": 17,
        "SELL": 3,
    }
    assert calibration["numeric_binding"] == "PASS_57_OF_57_AUTOMATIC"
    assert calibration["hold_default_bias_after"] == "NONE"
    assert calibration["sell_suppression_bias_after"] == "NONE"
    assert calibration["confidence_calibration"] == "PASS"
    assert calibration["timing_calibration"] == "PASS"
    assert calibration["decision_change_condition_quality"] == "PASS"
    assert calibration["hut_decision_taxonomy"] == "PASS"
    assert calibration["sell_positive_controls"] == "PASS_RXRX_TSLA_WULF"
    assert calibration["test_sink_delivery"] == ("PASS_20_OF_20_AFTER_RATE_LIMIT_CONTINUATION")
    assert calibration["test_sink_exact_payload_match"] is True
    assert calibration["production_recipient_send"] == 0
    assert calibration["production_delivery_intent_created"] == 0
    assert calibration["production_canary_enabled"] is False
    assert calibration["open_p0"] == []
    assert calibration["open_material_p1"] == []
    assert calibration["decision_canary_readiness"] == "PASS"
    assert calibration["canary_recommendation"] == "READY_WITH_OBSERVATION"
    assert state["contracts"]["cross_market_decision_calibration"] == (
        "PASS_CANARY_READY_WITH_OBSERVATION_CANARY_OFF"
    )
    assert state["contracts"]["cross_market_decision_quality_review"] == (
        "cross-market-decision-quality-review-v1"
    )
    assert state["contracts"]["evidence_maturity_pricing"] == (
        "evidence-maturity-pricing-v2"
    )
    assert state["contracts"]["scenario_asymmetry_confirmation_cost"] == (
        "scenario-asymmetry-confirmation-cost-v2"
    )
    assert state["contracts"]["preconfirmation_asymmetry_decision_engine"] == (
        "preconfirmation-asymmetry-decision-engine-v2"
    )
    assert state["contracts"]["legacy_technical_token_detection"] == (
        "legacy-technical-token-detection-v1"
    )
    assert state["contracts"]["us_market_digest_plan"] == ("us-market-digest-plan-v1")
    assert state["contracts"]["us_morning_exact_payload_quality"] == (
        "us-morning-exact-payload-quality-v1"
    )
    macro_quality = state["us_macro_zero_change_exact_payload_quality_repair"]
    assert macro_quality["status"] == "deployed_awaiting_natural_proof"
    assert macro_quality["historical_bad_payload_gate"] == "FAIL_AS_EXPECTED"
    assert macro_quality["quality_report_payload_hash_mismatch"] == 0
    assert macro_quality["test_market_message_count"] == 1
    assert macro_quality["test_stock_message_count"] == 0
    assert macro_quality["open_p0"] == []
    assert macro_quality["open_material_p1"] == []
    assert state["contracts"]["us_morning_full_message"] == ("us-morning-full-message-v1")
    assert state["contracts"]["us_price_structure_selective_rollout"] == (
        "us-price-structure-selective-rollout-v1"
    )
    assert state["contracts"]["us_price_structure_runtime_context"] == (
        "us-price-structure-runtime-context-v1"
    )
    assert state["contracts"]["market_evidence_utilization_validator"] == (
        "market-evidence-utilization-validator-v1"
    )
    assert state["contracts"]["kr_size_sector_message_selection"] == (
        "kr-size-sector-message-selection-repair-v1"
    )
    assert state["contracts"]["kr_market_preenable_test_send"] == (
        "kr-market-preenable-test-send-v1"
    )
    assert state["contracts"]["kr_price_structure_daily_history"] == (
        "kr-price-structure-daily-history-v1"
    )
    assert state["contracts"]["ohlcv_provider_limit_window_chaining"] == (
        "ohlcv-provider-limit-window-chaining-v1"
    )
    assert state["contracts"]["price_structure_coverage_degradation"] == (
        "price-structure-coverage-degradation-v1"
    )
    assert state["contracts"]["sr_nearest_user_visible_proximity"] == (
        "sr-nearest-user-visible-proximity-v1"
    )
    rollout = state["us_market_and_price_structure_rollout"]
    assert rollout["status"] == "enabled_awaiting_natural_proof"
    assert rollout["implementation_commit"] == ("1ba463571060a1fc9a5868afcdeab3de15f2bbe6")
    assert rollout["active_us_foreign_subjects"] == 13
    assert rollout["test_exact_payload_match"] == "PASS_14_OF_14"
    assert rollout["price_structure_replay"] == "PASS_13_OF_13"
    assert rollout["price_structure_eligibility"] == {
        "ELIGIBLE": 0,
        "ELIGIBLE_SR_ONLY": 13,
        "OMIT_PRICE_STRUCTURE": 0,
        "BLOCKED": 0,
    }
    assert rollout["us_price_structure_enabled"] is True
    assert rollout["post_enable_kr_price_structure_diff"] == 0
    assert rollout["open_p0"] == []
    assert rollout["open_material_p1"] == []
    current_data = state["price_structure_v3_current_data_shadow_message_validation"]
    assert current_data["status"] == "validated_ready_not_armed"
    assert current_data["target_sessions"] == {"kr": "2026-08-26", "us": "2026-08-25"}
    assert current_data["mandatory_controls"] == "10/10_PASS"
    assert current_data["current_runtime_visible_diff"] == 0
    assert current_data["production_enabled"] is False
    renderer = state["price_structure_v3_renderer_integration_micro_repair"]
    assert renderer["status"] == "integrated_ready_not_armed"
    assert renderer["implementation_commit"] == ("4246efb4f8afa3516402d1df7864967c177ac6e7")
    assert renderer["target_sessions"] == {"kr": "2026-08-26", "us": "2026-08-25"}
    assert renderer["fib_confluence_render_equivalence"] == "PASS"
    assert renderer["current_sr_stored_rule_separation"] == "PASS"
    assert renderer["legacy_technical_prose_policy"] == "PASS"
    assert renderer["message_eligibility_regression"] == 0
    assert renderer["numbers_without_provenance"] == 0
    assert renderer["production_enablement_ready"] == "YES"
    assert renderer["production_enabled"] is False
    detector = state["price_structure_v3_legacy_detector_false_positive_micro_repair"]
    assert detector["status"] == "integrated_ready_not_armed"
    assert detector["implementation_commit"] == detector_implementation_commit
    assert detector["target_sessions"] == {"kr": "2026-08-26", "us": "2026-08-25"}
    assert detector["rxrx_header_false_positive_root_cause"] == "PASS"
    assert detector["legacy_technical_token_policy"] == "PASS"
    assert detector["semantic_field_scoped_detection"] == "PASS"
    assert detector["protected_structural_fields"] == "PASS"
    assert detector["rxrx_false_rsi_match"] == 0
    assert detector["company_header_changed_by_legacy_suppression"] == 0
    assert detector["substring_only_technical_match"] == 0
    assert detector["nontechnical_prose_suppressed"] == 0
    assert detector["production_enablement_ready"] == "YES"
    assert detector["production_enabled"] is False
    assert state["contracts"]["market_context_adapter"] == ("market-context-adapter-v1")
    assert state["contracts"]["structured_market_context"] == ("structured-market-context-v1")
    assert state["contracts"]["nasdaq_official_exchange_breadth"] == (
        "nasdaq-official-exchange-breadth-v1"
    )
    assert state["contracts"]["kiwoom_kr_market_context"] == ("kiwoom-kr-market-context-v1")
    assert state["contracts"]["kr_market_flow_reconciliation"] == (
        "kr-market-flow-reconciliation-v1"
    )
    assert state["contracts"]["kr_market_flow_concentration"] == ("kr-market-flow-concentration-v1")
    assert state["contracts"]["message_quality_v2"] == "message-quality-v2"
    assert state["contracts"]["kr_market_internal_layout"] == ("kr-market-internal-layout-v1")
    assert state["contracts"]["market_research_seed_adapter"] == ("market-research-seed-adapter-v1")
    assert state["contracts"]["production_research_connector_boundary"] == (
        "production-research-connector-boundary-v1"
    )
    assert state["contracts"]["kr_investor_flow_participants"] == (
        "kr-investor-flow-participants-v1"
    )
    assert state["contracts"]["kr_investor_flow_reconciliation"] == (
        "kr-investor-flow-reconciliation-v1"
    )
    assert state["contracts"]["xkrx_role_target"] == "xkrx-role-target-v1"
    assert state["contracts"]["packet_bound_delivery_intent"] == ("packet-bound-delivery-intent-v1")
    assert state["contracts"]["kr_production_packet_persistence"] == (
        "kr-production-packet-persistence-v1"
    )
    assert state["contracts"]["shadow_cohort_readiness"] == ("shadow-cohort-readiness-v1")
    assert state["contracts"]["kr_orphan_delivery_reconciliation"] == (
        "kr-orphan-delivery-reconciliation-v1"
    )
    assert state["contracts"]["numeric_primary_owner"] == ("numeric-primary-owner-v1")
    assert state["contracts"]["cash_flow_capital_efficiency"] == ("cash-flow-capital-efficiency-v1")
    assert state["contracts"]["cash_flow_shadow_consumption"] == ("cash-flow-shadow-consumption-v1")
    assert state["contracts"]["cash_flow_runtime_shadow_canary"] == (
        "cash-flow-runtime-shadow-canary-v1"
    )
    assert state["contracts"]["baseline_cash_flow_claim_consistency"] == (
        "baseline-cash-flow-claim-consistency-v1"
    )
    assert state["contracts"]["cash_flow_user_visible"] == ("cash-flow-user-visible-v1")
    assert state["contracts"]["working_capital_evidence"] == ("working-capital-evidence-v1")
    assert state["contracts"]["working_capital_shadow_consumption"] == (
        "working-capital-shadow-consumption-v1"
    )
    assert state["contracts"]["working_capital_runtime_shadow_canary"] == (
        "working-capital-runtime-shadow-canary-v1"
    )
    assert state["contracts"]["working_capital_user_visible"] == ("working-capital-user-visible-v1")
    assert state["contracts"]["working_capital_user_visible_enable_gate"] == (
        "working-capital-user-visible-enable-gate-v1"
    )
    assert state["contracts"]["night_futures_attempt_archive"] == (
        "night-futures-attempt-archive-v1"
    )
    assert state["contracts"]["night_futures_publication_telemetry"] == (
        "night-futures-publication-telemetry-v1"
    )
    assert state["contracts"]["macro_digest_temporal_eligibility"] == (
        "macro-digest-temporal-eligibility-v1"
    )
    assert state["contracts"]["kr_market_digest_quality"] == ("kr-market-digest-quality-v1")
    assert state["contracts"]["entity_specific_synthesis"] == ("entity-specific-synthesis-v1")
    assert state["contracts"]["cross_message_synthesis_specificity"] == (
        "cross-message-synthesis-specificity-v1"
    )
    assert state["contracts"]["price_only_ai_anchor_packet"] == ("price-only-ai-anchor-packet-v1")
    assert state["contracts"]["variable_ai_swing_anchor_selection"] == (
        "variable-ai-swing-anchor-selection-v1"
    )
    assert state["contracts"]["ai_anchor_stability_policy"] == ("ai-anchor-stability-policy-v1")
    assert state["contracts"]["fibonacci_sr_ownership"] == ("fibonacci-sr-ownership-v1")
    assert state["contracts"]["canonical_swing_structure_candidate"] == (
        "canonical-swing-structure-candidate-v1"
    )
    assert state["contracts"]["fibonacci_valid_abstention"] == ("fibonacci-valid-abstention-v1")
    assert state["contracts"]["ai_anchor_consensus_policy"] == ("ai-anchor-consensus-policy-v1")
    assert state["contracts"]["variable_ai_swing_structure_consensus"] == (
        "variable-ai-swing-structure-consensus-v1"
    )
    assert state["contracts"]["price_structure_wave_fibonacci_v3"] == (
        "price-structure-wave-fibonacci-v3"
    )
    assert state["contracts"]["ohlcv_long_history"] == "ohlcv-long-history-contract-v1"
    assert state["contracts"]["primary_monthly_wave_hypothesis"] == (
        "primary-monthly-wave-hypothesis-v1"
    )
    assert state["contracts"]["wave_fibonacci_source_provenance"] == (
        "wave-fibonacci-source-provenance-v1"
    )
    assert state["contracts"]["multi_timeframe_sr_confluence_v3"] == (
        "multi-timeframe-sr-confluence-v3"
    )
    assert state["contracts"]["technical_zone_evidence_families"] == (
        "technical-zone-evidence-families-v1"
    )
    assert state["contracts"]["price_structure_v3_shadow_policy"] == (
        "price-structure-v3-shadow-policy-v1"
    )
    assert state["contracts"]["ohlcv_bar_completion"] == "ohlcv-bar-completion-v1"
    assert state["contracts"]["ohlcv_1200_backfill_cache"] == ("ohlcv-1200-backfill-cache-v1")
    assert state["contracts"]["wave_degree_current_cycle"] == ("wave-degree-current-cycle-v1")
    assert state["contracts"]["price_structure_v3_ai_feedback_loop"] == (
        "price-structure-v3-ai-feedback-loop-v1"
    )
    assert state["contracts"]["wave_hypothesis_equivalence_class"] == (
        "wave-hypothesis-equivalence-class-v1"
    )
    assert state["contracts"]["fib_family_endpoint_dependency"] == (
        "fib-family-endpoint-dependency-v1"
    )
    assert state["contracts"]["fib_family_consensus"] == ("fib-family-consensus-v1")
    assert state["contracts"]["family_consensus_membership_audit"] == (
        "family-consensus-membership-audit-v1"
    )
    assert state["contracts"]["price_structure_v3_ambiguity_set"] == (
        "price-structure-v3-ambiguity-set-v1"
    )
    assert state["contracts"]["family_filtered_confluence"] == ("family-filtered-confluence-v1")
    bounded_quality = state["kr_market_digest_us_entity_specific_synthesis_bounded_repair"]
    assert bounded_quality["instruction_commit"] == ("8cf5226ca0c5ae5553fb06b24399462ea3cf6088")
    assert bounded_quality["implementation_commit"] == ("f2326c39485e600bca2cee15747deeb8465c5c8a")
    assert bounded_quality["kr_domestic_context_rich"] is True
    assert bounded_quality["kr_market_digest_local_first"] == "pass"
    assert bounded_quality["kr_replay"] == "pass_8_of_8"
    assert bounded_quality["us_entity_specific_synthesis"] == "pass"
    assert bounded_quality["us_cross_industry_generic_repetition_before_after"] == [
        4,
        0,
    ]
    assert bounded_quality["us_replay"] == "pass_14_of_14"
    assert bounded_quality["hard_safety_errors"] == 0
    assert bounded_quality["open_p0"] == []
    assert bounded_quality["open_material_p1"] == []
    fibonacci_anchor = state["fibonacci_variable_ai_anchor_p1_closure"]
    assert fibonacci_anchor["instruction_commit"] == ("d9e6e2327f0f32256a1bd0d8caf2c0b0f1faf890")
    assert fibonacci_anchor["implementation_commit"] == ("9ac9a3cf2f6c759fa73ba5cbee6ab55c08ee1901")
    assert fibonacci_anchor["active_universe"] == 20
    assert fibonacci_anchor["benchmark_runs_per_packet"] == 5
    assert fibonacci_anchor["wider_universe_runs_per_packet"] == 3
    assert fibonacci_anchor["runtime_failures"] == 0
    assert fibonacci_anchor["semantic_rejected_timeframes"] == 4
    assert fibonacci_anchor["monthly_stability"]["material"] == 3
    assert fibonacci_anchor["weekly_stability"]["material"] == 11
    assert fibonacci_anchor["daily_stability"]["material"] == 10
    assert fibonacci_anchor["stock_user_visible_eligible"] == 8
    assert fibonacci_anchor["stock_user_visible_ineligible"] == 12
    assert fibonacci_anchor["material_anchor_omission"] == 0
    assert fibonacci_anchor["rich_packet_sufficiency"] == "PARTIAL"
    assert fibonacci_anchor["variable_ai_trial"] == "PARTIAL"
    assert fibonacci_anchor["code_correctness"] == "PASS"
    assert fibonacci_anchor["ai_fibonacci_multi_timeframe_structure"] == "SHADOW"
    assert fibonacci_anchor["production_enablement_ready"] == "NO"
    assert fibonacci_anchor["current_user_visible_message_diff"] == 0
    assert fibonacci_anchor["open_p0"] == []
    assert len(fibonacci_anchor["open_material_p1"]) == 2
    assert fibonacci_anchor["production_assist"] is False
    fibonacci_consensus = state["fibonacci_anchor_sr_consensus_final_p1_closure"]
    assert fibonacci_consensus["instruction_commit"] == ("39cab7ed8b1cb3bebea1bd1240498caa454bd09a")
    assert fibonacci_consensus["implementation_commit"] == prior_fibonacci_commit
    assert fibonacci_consensus["active_universe"] == 20
    assert fibonacci_consensus["benchmark_runs_per_packet"] == 5
    assert fibonacci_consensus["wider_universe_runs_per_packet"] == 3
    assert fibonacci_consensus["runtime_failures"] == 0
    assert fibonacci_consensus["semantic_rejected_timeframes"] == 0
    assert fibonacci_consensus["valid_abstentions"] == 56
    assert fibonacci_consensus["valid_abstentions_rejected"] == 0
    assert fibonacci_consensus["monthly_stability"]["material"] == 5
    assert fibonacci_consensus["weekly_stability"]["material"] == 7
    assert fibonacci_consensus["daily_stability"]["material"] == 1
    assert fibonacci_consensus["eligible_fibonacci_timeframes"] == 28
    assert fibonacci_consensus["omitted_unstable_timeframes"] == 13
    assert fibonacci_consensus["omitted_insufficient_timeframes"] == 19
    assert fibonacci_consensus["sr_runtime_variation"] == {
        "monthly": 0,
        "weekly": 0,
        "daily": 0,
    }
    assert fibonacci_consensus["prior_selected_structure_omissions"] == 0
    assert fibonacci_consensus["unstable_fibonacci_user_visible_eligible"] == 0
    assert fibonacci_consensus["production_enablement_ready"] == "YES"
    assert fibonacci_consensus["ai_fibonacci_multi_timeframe_structure"] == (
        "INTEGRATED_READY_NOT_ARMED"
    )
    assert fibonacci_consensus["current_user_visible_message_diff"] == 0
    assert fibonacci_consensus["open_p0"] == []
    assert fibonacci_consensus["open_material_p1"] == []
    assert fibonacci_consensus["production_assist"] is False
    price_structure_v3 = state["price_structure_wave_fibonacci_v3"]
    assert price_structure_v3["status"] == "integrated_ready_not_armed"
    assert price_structure_v3["instruction_commit"] == ("b0f81c8e16f588e314f93eb6097370e85f285241")
    assert price_structure_v3["implementation_commit"] == prior_price_structure_commit
    assert price_structure_v3["implementation_github_actions_run"] == 32945710995
    assert price_structure_v3["implementation_github_actions_status"] == ("passed_test_and_lint")
    assert price_structure_v3["active_universe"] == 20
    assert price_structure_v3["coverage"]["daily"] == {"pass": 14, "partial": 6}
    assert price_structure_v3["coverage"]["weekly"] == {
        "pass": 12,
        "partial": 7,
        "fail": 1,
    }
    assert price_structure_v3["coverage"]["monthly"] == {
        "pass": 8,
        "partial": 11,
        "fail": 1,
    }
    assert price_structure_v3["ai_runtime_calls"] == 11
    assert price_structure_v3["ai_runtime_decisions"] == 74
    assert price_structure_v3["focused_tests"] == "40_passed"
    assert price_structure_v3["full_tests"] == "1686_passed"
    assert price_structure_v3["ruff"] == "pass"
    assert price_structure_v3["ai_runtime_failures"] == 0
    assert price_structure_v3["ai_semantic_rejections"] == 0
    assert price_structure_v3["family_consensus_gates"]["dependency_mismatch"] == 0
    assert price_structure_v3["family_consensus_gates"]["tolerance_widening"] == 0
    assert price_structure_v3["family_consensus_gates"]["unstable_source_in_confluence"] == 0
    assert (
        price_structure_v3["sk_hynix_family_consensus"]["full_hypothesis_stability"]
        == "MATERIAL_VARIATION"
    )
    assert price_structure_v3["sk_hynix_family_consensus"]["family_level_price_structure"] == "PASS"
    assert price_structure_v3["true_conflict_controls"] == {
        "TSLA": "PASS_ZERO_SAFE_FAMILIES",
        "TSM_W3_DEPENDENCY": "PASS",
    }
    assert price_structure_v3["selected_but_not_fed_to_engine"] == 0
    assert price_structure_v3["unstable_fibonacci_user_visible_eligible"] == 0
    assert price_structure_v3["sk_hynix_reference"] == ("REFERENCE_MATCH_FAMILY_LEVEL_SAFE_SUBSET")
    assert price_structure_v3["price_structure_wave_fib_v3"] == ("INTEGRATED_READY_NOT_ARMED")
    assert price_structure_v3["price_structure_v3_family_consensus"] == (
        "INTEGRATED_READY_NOT_ARMED"
    )
    assert price_structure_v3["production_enablement_ready"] == "YES"
    assert price_structure_v3["open_p0"] == []
    assert price_structure_v3["open_material_p1"] == []
    assert price_structure_v3["current_user_visible_message_diff"] == 0
    assert price_structure_v3["production_assist"] is False
    preenablement = state["price_structure_v3_preenablement_micro_repair"]
    assert preenablement["instruction_commit"] == ("38b5fbca8a7264e3b73ef78c121b6ed6758c3ad8")
    assert preenablement["implementation_commit"] == preenablement_commit
    assert preenablement["membership_contract"] == ("family-consensus-membership-audit-v1")
    assert preenablement["consensus_membership_semantics"] == "PASS"
    assert preenablement["unjustified_alternative_in_consensus"] == 0
    assert preenablement["previous_stable_baseline_count"] == 7
    assert preenablement["previous_stable_evaluated_count"] == 7
    assert preenablement["previous_stable_regression_count"] == 0
    assert preenablement["diagnostic_alternative_control_012450"] == {
        "contamination": 0,
        "family_level_before": "FAIL",
        "family_level_after": "PASS",
    }
    assert preenablement["true_conflict_controls"] == {
        "TSLA": "PASS",
        "TSM_W3_DEPENDENCY": "PASS",
    }
    assert preenablement["knowledge"]["price_history_default"] == "1200/600/300"
    assert preenablement["technical_zone_display_formatting"] == "PASS"
    assert preenablement["raw_numeric_changed_by_display_formatter"] == 0
    assert preenablement["shadow_replay"] == {"kr": "7/7", "us_foreign": "13/13"}
    assert preenablement["production_enablement_ready"] == "YES"
    assert preenablement["open_p0"] == []
    assert preenablement["open_material_p1"] == []
    assert preenablement["current_user_visible_message_diff"] == 0
    assert preenablement["production_assist"] is False
    sr_completeness = state["price_structure_v3_sr_completeness_proximity_repair"]
    assert sr_completeness["instruction_commit"] == ("7267ca1d3e518d39986941bfda1d6447560db344")
    assert sr_completeness["implementation_commit"] == ("176f3e73eb097fac99f4038a8987b610954804cc")
    assert sr_completeness["contracts"] == {
        "base_layer": "deterministic-sr-base-layer-v1",
        "proximity_relevance": "sr-proximity-relevance-gate-v1",
    }
    assert sr_completeness["shadow_replay"] == {"kr": "7/7", "us_foreign": "13/13"}
    assert sr_completeness["remote_zone_promoted_as_nearest"] == 0
    assert sr_completeness["unexpected_empty_support"] == 0
    assert sr_completeness["unexpected_empty_resistance"] == 0
    assert sr_completeness["fabricated_sr_fill"] == 0
    assert sr_completeness["fallback_timeframe_relabel"] == 0
    assert sr_completeness["daily_resistance_audits"] == {
        "003690": "REPAIRED",
        "HUT": "REPAIRED",
    }
    assert sr_completeness["regressions"] == {
        "000660": 0,
        "012450": 0,
        "TSLA_unstable_fib": 0,
    }
    assert sr_completeness["production_enablement_ready"] == "YES"
    assert sr_completeness["open_p0"] == []
    assert sr_completeness["open_material_p1"] == []
    assert sr_completeness["current_user_visible_message_diff"] == 0
    advancement = state["phase_advancement_rule_v1"]
    assert advancement["p0_open"] == []
    assert advancement["p1_open"] == []
    assert advancement["phase_9_0a_ready"] is True
    assert advancement["phase_9_0a_complete"] is True
    assert advancement["phase_9_0b_ready"] is True
    assert advancement["phase_9_0b_complete"] is True
    assert advancement["phase_9_0c_ready"] is True
    assert advancement["phase_9_0c_complete"] is True
    assert advancement["phase_9_0d_ready"] is True
    assert advancement["phase_9_0d_runtime_implementation_complete"] is True
    assert advancement["phase_9_0d_natural_proof"] == "live_pass_run30"
    assert advancement["phase_9_0d_1_complete"] is True
    assert advancement["phase_9_0e_ready"] is True
    assert advancement["phase_9_0e_implementation_complete"] is True
    assert advancement["phase_9_0e_operating_enabled"] is True
    assert advancement["phase_9_0e_natural_proof"] == "pending_next_natural_us"
    assert advancement["phase_9_1a_complete"] is True
    assert advancement["phase_9_1b_ready"] is True
    assert advancement["phase_9_1b_scope"] == ("SELECTIVE_INVENTORY_AR_AP_CANONICAL_CORE")
    assert advancement["phase_9_1b_complete"] is True
    assert advancement["phase_9_1c_ready"] is True
    assert advancement["phase_9_1c_scope"] == (
        "WORKING_CAPITAL_SHADOW_CONSUMPTION_EARNINGS_QUALITY"
    )
    assert advancement["phase_9_1c_complete"] is True
    assert advancement["phase_9_1d_ready"] is True
    assert advancement["phase_9_1d_scope"] == (
        "SELECTIVE_RUNTIME_SHADOW_CANARY_INVENTORY_EXACT_TRADE_AR"
    )
    assert advancement["phase_9_1d_deployed"] is True
    assert advancement["phase_9_1d_natural_proof"] == (
        "inventory_live_pass_run32_trade_ar_not_observed"
    )
    assert advancement["phase_9_1e_architecture_ready"] is True
    assert advancement["phase_9_1e_preintegration_complete"] is True
    assert advancement["phase_9_1e_user_visible_mode"] == "OFF"
    assert advancement["phase_9_1e_inventory_enablement"] == ("YES_INVENTORY_ONLY")
    assert advancement["phase_9_1e_trade_ar_enablement"] == ("NO_PENDING_NATURAL")
    assert advancement["phase_9_1e_1_implementation_complete"] is True
    assert advancement["phase_9_1e_1_inventory_only_rollout_ready"] is True
    assert advancement["phase_9_1e_1_operating_enabled"] is True
    assert advancement["phase_9_1e_1_user_visible_mode"] == "SELECTIVE_INVENTORY"
    assert advancement["phase_9_1e_1_inventory_user_visible"] == ("ENABLED_PENDING_NATURAL")
    assert advancement["phase_9_1e_1_trade_ar_user_visible"] == ("OFF_PENDING_NATURAL_PROOF")
    assert advancement["next_major_architecture_ready"] is False
    producer_repair = state["kr_non_trading_day_producer_repair"]
    assert producer_repair["status"] == "deployed_pending_natural"
    assert producer_repair["source_run_id"] == 33
    assert producer_repair["source_packet_artifacts"] == 0
    assert producer_repair["stage_a_reported_stock_rows"] == 7
    assert producer_repair["companion_digest_rows"] == 1
    assert producer_repair["reconciled_rows"] == 8
    assert producer_repair["sent_rows"] == 0
    assert producer_repair["sent_at_set"] == 0
    assert producer_repair["p0_open"] == []
    assert producer_repair["p1_open"] == []
    macro_temporal = state["macro_digest_temporal_repair"]
    assert macro_temporal["status"] == "deployed_pending_natural"
    assert macro_temporal["root_cause_branch"] == "B"
    assert macro_temporal["instruction_commit"] == ("951558c0ec79f84b739eff1cbafd2870eb6f3fba")
    assert macro_temporal["implementation_commit"] == ("68a6c39a098380d8a22de5b4d784c730818e9b04")
    assert macro_temporal["false_today_claims_after"] == 0
    assert macro_temporal["open_p0"] == 0
    assert macro_temporal["open_material_p1"] == 0
    shadow_gate = state["kr_shadow_gate_packet_repair"]
    assert shadow_gate["status"] == "deployed_pending_natural"
    assert shadow_gate["root_cause_branch"] == "C"
    assert shadow_gate["instruction_commit"] == ("7da8d8866a9b7aafc8c010424cdbc4192de46cbb")
    assert shadow_gate["implementation_commit"] == ("64086c4af7735dcbe2fd3f5093f4167952a280e0")
    assert shadow_gate["source_run_id"] == 36
    assert shadow_gate["source_analysis"] == "7_of_7"
    assert shadow_gate["replay_packet_count"] == 1
    assert shadow_gate["replay_delivery_intents"] == 8
    assert shadow_gate["replay_fallback_eligible"] == 8
    assert shadow_gate["replay_duplicate_packets"] == 0
    assert shadow_gate["replay_duplicate_intents"] == 0
    assert shadow_gate["p0_open"] == []
    assert shadow_gate["p1_open"] == []
    common_ai_core = state["common_ai_core_v1"]
    assert common_ai_core["status"] == "integrated_canary_pending_natural"
    assert common_ai_core["production_assist_control_plane"] == "B"
    assert common_ai_core["existing_ai_review_pilot_enabled"] is True
    assert common_ai_core["us_run37_free_analyst"] == "14/14"
    assert common_ai_core["us_run37_adaptive"] == "14/14"
    assert common_ai_core["kr_replay"] == "8/8"
    assert common_ai_core["canary_simulated_selected"] == 3
    assert common_ai_core["canary_runtime_quality"] == "passed"
    assert common_ai_core["production_assist"] is False
    assert common_ai_core["free_analyst_adaptive_enabled"] is True
    assert common_ai_core["free_analyst_adaptive_mode"] == ("free_analyst_adaptive_canary")
    assert common_ai_core["free_analyst_adaptive_canary"] == ("enabled_pending_natural")
    assert common_ai_core["free_analyst_adaptive_full"] == "off"
    assert common_ai_core["kr_canary_natural"] == "not_observed"
    assert common_ai_core["us_canary_natural"] == "not_observed"
    assert common_ai_core["open_research_production_integration"] == 0
    assert common_ai_core["open_p0"] == []
    assert common_ai_core["open_material_p1"] == []
    structured_quality = state["structured_data_quality_v2"]
    assert structured_quality["kr_structured_acquisition"] == "PARTIAL"
    assert structured_quality["us_structured_acquisition"] == "PARTIAL"
    assert structured_quality["kr_structured_context_value_add"] == ("NO_MATERIAL_VALUE")
    assert structured_quality["us_structured_context_value_add"] == "PASS"
    assert structured_quality["common_message_quality_v2"] == "PASS"
    assert structured_quality["production_ready"] == "YES"
    market_adapter = state["common_market_adapter_v1"]
    assert market_adapter["status"] == "structured_quality_v2_pending_natural"
    assert market_adapter["common_contract"] == "PASS"
    assert market_adapter["kr_adapter"] == "PARTIAL"
    assert market_adapter["us_adapter"] == "PARTIAL"
    assert market_adapter["fact_boundary"] == "PASS"
    assert market_adapter["hidden_arithmetic"] == 0
    assert market_adapter["unit_conflicts"] == 0
    assert market_adapter["temporal_errors"] == 0
    assert market_adapter["production_research_connector"] == "NOT_AVAILABLE"
    assert market_adapter["open_research_live_canary"] == "BLOCKED_CONNECTOR"
    assert market_adapter["open_research_production_integration"] == 0
    assert market_adapter["structured_adapter_production"] == ("DEPLOYED_PENDING_NATURAL")
    assert market_adapter["open_p0"] == []
    assert market_adapter["open_material_p1"] == []
    phase_90a = state["phase_9_0a_cash_flow_capital_efficiency"]
    assert phase_90a["status"] == "architecture_closed_ready_for_phase_9_0b"
    assert phase_90a["active_universe"] == 20
    assert phase_90a["phase_9_0b_ready"] is True
    assert phase_90a["runtime_behavior_changed"] is False
    assert phase_90a["user_visible_integration"] is False
    phase_90b = state["phase_9_0b_canonical_cash_flow_core"]
    assert phase_90b["status"] == ("canonical_core_implemented_shadow_ready_for_phase_9_0c")
    assert phase_90b["active_universe"] == 20
    assert phase_90b["derived_fcf_facts"] == 191
    assert phase_90b["derived_fcf_complete_lineage_pct"] == 100
    assert phase_90b["phase_9_0c_ready"] is True
    assert phase_90b["runtime_behavior_changed"] is False
    assert phase_90b["user_visible_integration"] is False
    phase_90c = state["phase_9_0c_cash_flow_shadow_consumption"]
    assert phase_90c["status"] == "closed_retrospective_ready_for_phase_9_0d"
    assert phase_90c["active_universe"] == 20
    assert phase_90c["consumption_eligible"] == 12
    assert phase_90c["shadow_used"] == 10
    assert phase_90c["semantic_errors"] == 0
    assert phase_90c["phase_9_0d_ready"] is True
    assert phase_90c["runtime_behavior_changed"] is False
    assert phase_90c["user_visible_integration"] is False
    phase_90d = state["phase_9_0d_cash_flow_runtime_shadow_canary"]
    assert phase_90d["status"] == "live_pass_selective_subset"
    assert phase_90d["work_instruction_commit"] == ("a24e4f2210f944fa7c43d8dbf8be1d1a8e652164")
    assert phase_90d["production_isolation"] == "passed"
    assert phase_90d["natural_us_canary"] == (
        "complete_pass_run30_9_full_fcf_1_ocf_only_0_influence"
    )
    assert phase_90d["phase_9_0e_ready"] is True
    assert phase_90d["user_visible_integration"] is False
    phase_90d1 = state["phase_9_0d_1_baseline_cash_flow_consistency"]
    assert phase_90d1["status"] == "baseline_cash_flow_consistency_closed"
    assert phase_90d1["root_cause_severity_before_repair"] == "P0"
    assert phase_90d1["post_repair_cross_artifact_errors"] == 0
    assert phase_90d1["phase_9_0e_ready"] is True
    assert phase_90d1["cash_flow_user_visible"] is False
    phase_90e = state["phase_9_0e_cash_flow_user_visible_integration"]
    assert phase_90e["status"] == "deployed_selective_pending_natural"
    assert phase_90e["work_instruction_commit"] == ("309f5f1756d39d5972c5d4b48faaeab4862d8077")
    assert phase_90e["implementation_commit"] == ("cf3194981124de2a6f85fbe81b145ef06e1db08d")
    assert phase_90e["preview_selected"] == 9
    assert phase_90e["ai_fallback_parity_errors"] == 0
    assert phase_90e["cash_flow_user_visible_rollout_ready"] is True
    assert phase_90e["next_major_architecture_ready"] is True
    phase_91a = state["phase_9_1a_working_capital_evidence_architecture"]
    assert phase_91a["status"] == "architecture_closed_promoted"
    assert phase_91a["work_instruction_commit"] == ("eaaadb1ac4fb5c9a7d3486ecc8274708c285ff79")
    assert phase_91a["implementation_commit"] == ("0d3b42715fc8964fe053d72e0ecc979fb78b14cc")
    assert phase_91a["active_universe"] == 20
    assert phase_91a["metric_coverage"]["inventory"]["eligible"] == 11
    assert phase_91a["runtime_user_visible_diff"] == 0
    assert phase_91a["phase_9_1b_ready"] is True
    phase_91b = state["phase_9_1b_canonical_working_capital_core"]
    assert phase_91b["status"] == "implemented_shadow_promoted"
    assert phase_91b["work_instruction_commit"] == ("0952bee040133aa49a4ba494ecae76163e9a9511")
    assert phase_91b["implementation_commit"] == ("a35c615a77b44b37739d4f6a73aa9f0f290ba831")
    assert phase_91b["implementation_github_actions_run"] == 32450301567
    assert phase_91b["implementation_github_actions_status"] == ("passed_test_and_lint")
    assert phase_91b["active_universe"] == 20
    assert phase_91b["canonical_fact_counts"] == {
        "reported_selected": 160,
        "balance_delta": 44,
        "balance_yoy": 44,
        "flow_yoy": 31,
        "eligible_relations": 53,
    }
    assert phase_91b["coverage_newly_blocked"] == 0
    assert phase_91b["arithmetic_errors"] == 0
    assert phase_91b["provenance_errors"] == 0
    assert phase_91b["idempotency_errors"] == 0
    assert phase_91b["runtime_user_visible_diff"] == 0
    assert phase_91b["phase_9_1c_ready"] is True
    phase_91c = state["phase_9_1c_working_capital_shadow_consumption"]
    assert phase_91c["status"] == "shadow_consumption_closed_retrospective_promoted"
    assert phase_91c["work_instruction_commit"] == ("613d91d74d3a91c43ed61f98a13a2ca57b7a90ae")
    assert phase_91c["active_universe"] == 20
    assert phase_91c["selected_relations"] == {
        "inventory": 5,
        "exact_trade_ar": 2,
        "broad_ar": 0,
        "exact_trade_ap": 0,
        "broad_ap": 0,
    }
    assert phase_91c["numeric_binding"]["automatic"] == 7
    assert phase_91c["numeric_binding"]["manual"] == 0
    assert phase_91c["semantic_mislabels"] == 0
    assert phase_91c["causal_overclaims"] == 0
    assert phase_91c["unknown_contradictions"] == 0
    assert phase_91c["human_quality"]["degraded"] == 0
    assert phase_91c["runtime_user_visible_diff"] == 0
    assert phase_91c["phase_9_1d_ready"] is True
    phase_91d = state["phase_9_1d_working_capital_runtime_shadow_canary"]
    assert phase_91d["status"] == "live_pass_inventory_trade_ar_not_observed"
    assert phase_91d["work_instruction_commit"] == ("dc4e1cf14faa7cebf78eb8ba5a5e73b6369c991c")
    assert phase_91d["implementation_commit"] == ("5316113062782b09595a495ec9a903a4973f9df5")
    assert phase_91d["allowed_metrics"] == [
        "inventory",
        "trade_accounts_receivable",
    ]
    assert phase_91d["retrospective_selected_relations"] == {
        "inventory": 5,
        "exact_trade_ar": 2,
        "broad_ar": 0,
        "exact_trade_ap": 0,
        "broad_ap": 0,
    }
    assert phase_91d["production_influence"] == 0
    assert phase_91d["inventory_natural_proof"] == "LIVE_PASS_RUN32"
    assert phase_91d["trade_ar_natural_proof"] == "NOT_OBSERVED"
    assert phase_91d["phase_9_1e_architecture_ready"] is True
    phase_91e = state["phase_9_1e_working_capital_user_visible_preintegration"]
    assert phase_91e["status"] == "preintegration_complete_pending_natural"
    assert phase_91e["work_instruction_commit"] == ("99f7e86f3ae40cc86a4865ef70dc89abf79d5a37")
    assert phase_91e["implementation_commit"] == ("a4f8570130d1fd33f802d391c6a196d1c5579278")
    assert phase_91e["preview_selected_relations"] == {
        "inventory": 3,
        "exact_trade_ar": 2,
        "broad_ar": 0,
        "ap": 0,
    }
    assert phase_91e["inventory_natural_proof"] == "LIVE_PASS_RUN32"
    assert phase_91e["trade_ar_natural_proof"] == "NOT_OBSERVED"
    assert phase_91e["working_capital_user_visible_mode"] == "OFF"
    assert phase_91e["runtime_user_visible_diff"] == 0
    assert phase_91e["phase_9_1e_preintegration_ready"] is True
    phase_91e1 = state["phase_9_1e_1_inventory_only_user_visible_enablement"]
    assert phase_91e1["status"] == "deployed_inventory_only_pending_natural"
    assert phase_91e1["work_instruction_commit"] == ("880e7a9834439971f53b8a7bc0712d0ece26854d")
    assert phase_91e1["inventory_natural_proof"] == "LIVE_PASS_RUN32"
    assert phase_91e1["trade_ar_natural_proof"] == "NOT_OBSERVED"
    assert phase_91e1["inventory_selected"] == 3
    assert phase_91e1["trade_ar_selected"] == 0
    assert phase_91e1["ai_fallback_parity_errors"] == 0
    assert phase_91e1["inventory_only_rollout_ready"] is True
    assert phase_91e1["working_capital_user_visible_mode"] == "SELECTIVE_INVENTORY"
    assert phase_91e1["inventory_user_visible"] == "ENABLED_PENDING_NATURAL"
    assert phase_91e1["trade_ar_user_visible"] == "OFF_PENDING_NATURAL_PROOF"
    assert phase_91e1["operating_health"] == "PASS"
    assert phase_91e1["operating_smoke"] == "65_PASSED"
    investor_flow = state["kr_investor_flow_reconciliation_repair"]
    assert investor_flow["status"] == "complete_pending_natural_confirmation"
    assert investor_flow["work_instruction_commit"] == ("e9d7c73cf6f25b2423b55a6899465e86441316d1")
    assert investor_flow["implementation_commit"] == ("47fc87e2a9189556a7206065fdb759f3603ce497")
    assert investor_flow["complete_windows"] == 21
    assert investor_flow["unsupported_attribution_before_after"] == [2, 0]
    assert investor_flow["public_schema_diff"] == 0
    assert investor_flow["p0_open"] == []
    assert investor_flow["p1_open"] == []
    night_telemetry = state["night_futures_publication_telemetry_repair"]
    assert night_telemetry["status"] == "repair_deployed_pending_natural"
    assert night_telemetry["instruction_commit"] == ("b7cf6a2f413e309bb637e524aeb7c1436e4c5b1b")
    assert night_telemetry["implementation_commit"] == ("d54f1102c02c9ff1c6a8ddd18fc40d1aea059caf")
    assert night_telemetry["observer_slots_kst"] == ["08:45", "09:15"]
    assert night_telemetry["deadline_verdict"] == "DEADLINE_UNPROVEN"
    assert night_telemetry["fail_closed_safety"] == "PASS"
    assert night_telemetry["user_visible_behavior_diff"] == 0
    assert state["persistent_gaps"]["krx_open_api"] == (
        "APPROVED_TELEMETRY_ONLY_OPERATING_USER_VISIBLE_NOT_INTEGRATED"
    )
    assert state["krx"]["exact_slot_capture"] == ("operating_telemetry_only_pending_natural")
    assert state["krx"]["user_visible_integration"] is False
    assert state["persistent_gaps"]["night_futures_session_basis"] == (
        "CLOSED_RETROSPECTIVE_LIVE_FAIL_CLOSED_RUN28"
    )
    assert state["persistent_gaps"]["night_futures_preceding_day_calendar_lookup"] == (
        "CLOSED_RETROSPECTIVE_PENDING_NATURAL"
    )
    assert state["persistent_gaps"]["night_futures_publication_attempt_telemetry"] == (
        "REPAIR_DEPLOYED_PENDING_NATURAL_DEADLINE_UNPROVEN"
    )
    assert (
        state["persistent_gaps"]["fallback_price_lifecycle"]
        == "CLOSED_RETROSPECTIVE_AND_OPERATING_CODE_PROMOTED"
    )
    master = state["master_market_validation_price_structure_rollout"]
    assert master["status"] == "natural_us_reproof_pending_kr_live_pass"
    assert master["instruction_commit"] == ("e76a7d6b5e8ddc110d3228cfd5e55f26dbdb1e1d")
    assert master["integration_code_commit"] == implementation_commit
    assert master["track_a"]["status"] == "replay_pass_natural_reproof_pending"
    assert master["track_a"]["natural_run_id"] == 41
    assert master["track_a"]["natural_packet"] == ("2026-08-27-us-run-41-ae4f42c23abc")
    assert master["track_a"]["open_material_p1"] == []
    assert master["track_b"]["status"] == "live_pass_run42"
    assert master["track_b"]["natural_run_id"] == 42
    assert master["track_b"]["target_session"] == "2026-08-27"
    assert master["track_b"]["natural_packet"] == ("2026-08-27-kr-run-42-5d8d23e6fbd6")
    assert master["track_b"]["natural_route"] == "ai_assisted"
    assert master["track_b"]["natural_reproof"] == "PASS"
    assert master["track_b"]["open_material_p1"] == []
    assert master["track_c"] == {
        "status": "do_not_start",
        "branch": None,
        "production_armed": False,
    }
    assert master["price_structure_v3"] == "integrated_ready_not_armed"
    assert master["open_p0"] == []
    assert master["open_material_p1"] == []
    assert master["production_assist"] is False
    bounded_repair = state["kr_bounded_local_first_numeric_registry_repair"]
    assert bounded_repair["status"] == "live_pass_run42"
    assert bounded_repair["instruction_commit"] == ("f6ba660048d3fa520e3aeb43d04036c119764292")
    assert bounded_repair["integration_code_commit"] == kr_integration_commit
    assert bounded_repair["numeric_paths"] == {
        "total": 1989,
        "registered": 1989,
        "unsupported": 0,
        "prose_allowed": 1499,
        "denied": 490,
    }
    assert bounded_repair["open_p0"] == []
    assert bounded_repair["open_material_p1"] == []
    assert bounded_repair["natural_kr_reproof"] == "PASS"
    assert bounded_repair["track_c"] == "DO_NOT_START"
    us_natural = state["us_morning_natural_market_data_review"]
    assert us_natural["status"] == "material_p1_found_stop"
    assert us_natural["natural_run_id"] == 41
    assert us_natural["target_session"] == "2026-08-26"
    assert us_natural["delivery"] == "14/14_exactly_once"
    assert us_natural["material_information_loss_count"] == 7
    assert us_natural["open_p0"] == []
    assert us_natural["open_material_p1"] == [
        "us_current_session_market_evidence_omitted_from_natural_digest"
    ]
    assert us_natural["next_action"] == "BOUNDED_US_MARKET_REPAIR"
    us_repair = state["us_bounded_current_session_market_evidence_repair"]
    assert us_repair["status"] == "replay_pass_natural_reproof_pending"
    assert us_repair["integration_code_commit"] == implementation_commit
    assert us_repair["historical_digest_validator"] == "FAIL_AS_EXPECTED"
    assert us_repair["repaired_ai_utilization"] == "PASS"
    assert us_repair["repaired_fallback_utilization"] == "PASS"
    assert us_repair["ai_fallback_plan_divergence"] == 0
    assert us_repair["material_information_loss"] == 0
    assert us_repair["open_p0"] == []
    assert us_repair["open_material_p1"] == []
    assert us_repair["natural_us_reproof"] == "PENDING"
    assert us_repair["price_structure_track_c"] == "DO_NOT_START"
    assert us_repair["price_structure_v3"] == "INTEGRATED_READY_NOT_ARMED"
    assert us_repair["next_action"] == "WAIT_FOR_NEXT_NATURAL_US_MORNING"
    kr_natural = state["kr_afternoon_natural_market_data_reproof"]
    assert kr_natural["status"] == "live_pass"
    assert kr_natural["instruction_commit"] == ("107f40b0b6b7e794f420534e71b69af0c969e643")
    assert kr_natural["producer_operating_sha"] == ("a1fb1a7006109f8699e03997662bde27db5ad464")
    assert kr_natural["natural_run_id"] == 42
    assert kr_natural["target_session"] == "2026-08-27"
    assert kr_natural["packet_id"] == "2026-08-27-kr-run-42-5d8d23e6fbd6"
    assert kr_natural["delivery"] == "8/8_exactly_once"
    assert kr_natural["exact_message_payload_match"] == "PASS"
    assert kr_natural["numeric_registry"] == "1989/1989_REGISTERED_UNSUPPORTED_0"
    assert kr_natural["local_first_digest"] == "PASS"
    assert kr_natural["natural_kr_reproof"] == "PASS"
    assert kr_natural["price_structure_track_c"] == "DO_NOT_START"
    assert kr_natural["open_p0"] == []
    assert kr_natural["open_material_p1"] == []
    kr_size_sector = state["kr_size_sector_message_selection_bounded_repair"]
    assert kr_size_sector["status"] == "live_pass_run_now"
    assert kr_size_sector["instruction_commit"] == ("794c6f5d956d0928eac0113d658fede58b1266dc")
    assert kr_size_sector["implementation_commit"] == kr_size_sector_implementation
    assert kr_size_sector["historical_message_new_policy"] == "FAIL_AS_EXPECTED"
    assert kr_size_sector["repaired_ai_utilization"] == "PASS"
    assert kr_size_sector["repaired_fallback_utilization"] == "PASS"
    assert kr_size_sector["selected_size_refs"] == 6
    assert kr_size_sector["selected_sector_refs"] == 4
    assert kr_size_sector["unregistered_size_sector_numeric"] == 0
    assert kr_size_sector["material_information_loss"] == 0
    assert kr_size_sector["open_p0"] == []
    assert kr_size_sector["open_material_p1"] == []
    assert kr_size_sector["natural_kr_reproof"] == ("LIVE_PASS_PACKET_E4CF532E619B")
    assert kr_size_sector["next_action"] == "CLOSED_BY_RUN_NOW_LIVE_PROOF"
    preenable = state["kr_market_preenable_test_send_and_bounded_enablement"]
    assert preenable["status"] == "blocked_no_safe_test_sink"
    assert preenable["instruction_commit"] == ("f161bc1c724cfd431efaaa458af61e02a378daeb")
    assert preenable["implementation_commit"] == preenable_implementation
    assert preenable["data_collection"] == "PASS_STORED_PRODUCTION_PACKET_42_OF_42"
    assert preenable["numeric_gate"] == "PASS"
    assert preenable["candidate_quality"] == "PASS"
    assert preenable["test_sink_available"] is False
    assert preenable["test_send"] == "BLOCKED_NO_SAFE_SINK"
    assert preenable["test_delivery_count"] == 0
    assert preenable["production_delivery_intent_created"] == 0
    assert preenable["runtime_gate_type"] == "ALREADY_ACTIVE_BY_CODE_DEFAULT"
    assert preenable["enablement_action"] == "DO_NOT_ENABLE"
    assert preenable["open_p0"] == []
    assert preenable["open_material_p1"] == ["dedicated_test_sink_not_configured"]
    rollout = state["kr_top3_sector_price_structure_selective_preenablement"]
    assert rollout["status"] == "blocked_no_safe_test_sink"
    assert rollout["instruction_commit"] == ("0c95ddc9be319dbacc5ce1d824802e0c3c72fed1")
    assert rollout["implementation_commit"] == top3_implementation
    assert rollout["implementation_github_actions_run"] == 33071858051
    assert rollout["track_a"] == "implemented_default_off"
    assert rollout["track_b"] == "implemented_default_off"
    assert rollout["track_c"] == "blocked_no_safe_test_sink"
    assert rollout["track_d"] == "not_started"
    assert rollout["price_structure_sr_only"] == 7
    assert rollout["test_delivery_count"] == 0
    assert rollout["production_delivery_intent_created"] == 0
    assert rollout["kr_market_top3_enablement"] == "DO_NOT_ENABLE"
    assert rollout["kr_price_structure_enablement"] == "DO_NOT_ENABLE"
    assert rollout["us_price_structure_enabled"] is False
    assert rollout["runtime_user_visible_diff"] == 0
    assert rollout["open_p0"] == []
    assert rollout["open_material_p1"] == ["dedicated_test_sink_not_configured"]
    price_structure_repair = state["kr_price_structure_daily_history_nearest_repair"]
    assert price_structure_repair["status"] == ("replay_pass_ready_for_preenable")
    assert price_structure_repair["instruction_commit"] == (
        "0a8dae7eeca7126844094f0aebcc7a7df0bea606"
    )
    assert price_structure_repair["track_a_commit"] == ("da82d89c2e1c3bc125442128da1573d532263d74")
    assert price_structure_repair["track_b_commit"] == ("83f3d643bc2cb40d9039c1d965647d01a43769e2")
    assert price_structure_repair["integration_code_commit"] == (
        price_structure_repair_implementation
    )
    assert price_structure_repair["implementation_github_actions_status"] == (
        "passed_test_and_lint"
    )
    assert price_structure_repair["daily_zero_root_cause"] == ("provider_parameter_bug")
    assert price_structure_repair["daily_subjects_partial_provider_limit"] == 7
    assert price_structure_repair["synthetic_daily_bars"] == 0
    assert price_structure_repair["old_000660_render_new_validator"] == ("fail_as_expected")
    assert price_structure_repair["current_validator_errors"] == 0
    assert price_structure_repair["open_p0"] == []
    assert price_structure_repair["open_material_p1"] == []
    assert price_structure_repair["kr_price_structure"] == ("INTEGRATED_READY_NOT_ARMED")
    assert price_structure_repair["runtime_enablement"] is False
    assert price_structure_repair["test_send"] is False
    daily_1200 = state["kr_price_structure_daily_1200_extension_or_degradation"]
    assert daily_1200["status"] == "replay_pass_ready_for_preenable"
    assert daily_1200["instruction_commit"] == ("3e42f3fad2e32ff1b3cca47861cfb9704095ce28")
    assert daily_1200["track_a_commit"] == ("c9e8fc1e25394857bd88d4652e3a8b1e88638011")
    assert daily_1200["track_b_commit"] == ("d60b7b2a9edecbad0ed54c2151ecfba163478522")
    assert daily_1200["integration_code_commit"] == daily_1200_implementation
    assert daily_1200["implementation_github_actions_run"] == 33081793581
    assert daily_1200["implementation_github_actions_status"] == ("passed_test_and_lint")
    assert daily_1200["provider_capability"] == ("PROVIDER_HARD_LIMIT_NO_OLDER_WINDOW")
    assert daily_1200["implementation_path"] == "VERIFIED_PARTIAL_SAFE_1000"
    assert daily_1200["daily_canonical_target"] == 1200
    assert daily_1200["daily_provider_request_limit"] == 1000
    assert daily_1200["daily_subjects_partial_safe"] == 7
    assert daily_1200["unexplained_daily_shortfall"] == 0
    assert daily_1200["open_p0"] == []
    assert daily_1200["open_material_p1"] == []
    assert daily_1200["runtime_enablement"] is False
    assert daily_1200["operating_promotion"] is False
    final_preenable = state["kr_top3_price_structure_final_preenable_and_enable"]
    assert final_preenable["status"] == "blocked_no_test_sink"
    assert final_preenable["instruction_commit"] == ("9f37cfad97487876d6dfa63c03750f4dab664dbf")
    assert final_preenable["track_a_commit"] == ("05b57901f7cf25086b580510aac6a6e72329cdfc")
    assert final_preenable["track_a_github_actions_run"] == 33085141564
    assert final_preenable["track_a_github_actions_status"] == ("passed_test_and_lint")
    assert final_preenable["track_a"] == "BLOCKED_NO_TEST_SINK"
    assert final_preenable["track_b"] == "NOT_RUN_TRACK_A_BLOCKED"
    assert final_preenable["track_c"] == "NOT_RUN_TRACK_A_BLOCKED"
    assert final_preenable["test_sink_available"] is False
    assert final_preenable["test_delivery_count"] == 0
    assert final_preenable["operating_promotion"] is False
    assert final_preenable["kr_market_top3_enabled"] is False
    assert final_preenable["kr_price_structure_enabled"] is False
    assert final_preenable["us_price_structure_enabled"] is False
    assert final_preenable["open_p0"] == []
    assert final_preenable["open_material_p1"] == ["dedicated_test_sink_not_configured"]
    assert final_preenable["kr_rollout"] == "NOT_ENABLED"
    resume = state["kr_test_sink_configuration_and_final_preenable_resume"]
    assert resume["status"] == "enabled_live_pass"
    assert resume["instruction_commit"] == ("68ede1eae42315d94a89023fbc6c1f9be07fc99d")
    assert resume["implementation_commit"] == ("315081005198e7b5676e9383f10d4a52b3d3ca34")
    assert resume["implementation_github_actions_run"] == 33094185080
    assert resume["implementation_github_actions_status"] == ("passed_test_and_lint")
    assert resume["test_sink_available"] is True
    assert resume["test_production_sink_collision"] == 0
    assert resume["test_production_intent_collision"] == 0
    assert resume["test_delivery_count"] == 8
    assert resume["test_exact_payload_match"] == "PASS_8_OF_8"
    assert resume["production_delivery_intent_created"] == 0
    assert resume["operating_promotion"] is True
    assert resume["kr_market_top3_enabled"] is True
    assert resume["kr_price_structure_enabled"] is True
    assert resume["us_price_structure_enabled"] is False
    assert resume["open_p0"] == []
    assert resume["open_material_p1"] == []
    assert resume["kr_rollout"] == "LIVE_PASS"
    assert resume["next_action"] == "NO_ACTION_KR_LIVE_PROOF_CLOSED"
    formatting = state["kr_market_internal_linebreak_formatting_micro_repair"]
    assert formatting["status"] == "live_pass"
    assert formatting["instruction_commit"] == ("dd1b5eb712081c222bcfe1b4465d4fe0aac5f89a")
    assert formatting["implementation_commit"] == ("03a418ab1f616d0063becf3928a1327056dd2d66")
    assert formatting["implementation_github_actions_run"] == 33099146372
    assert formatting["implementation_github_actions_status"] == ("passed_test_and_lint")
    assert formatting["test_market_message_count"] == 1
    assert formatting["test_stock_message_count"] == 0
    assert formatting["test_exact_payload_match"] == "PASS_1_OF_1"
    assert formatting["production_recipient_send"] == 0
    assert formatting["production_delivery_intent_created"] == 0
    assert formatting["data_value_diff"] == 0
    assert formatting["top3_ranking_diff"] == 0
    assert formatting["numeric_provenance_diff"] == 0
    assert formatting["kr_market_top3_enabled"] is True
    assert formatting["kr_price_structure_enabled"] is True
    assert formatting["us_price_structure_enabled"] is False
    assert formatting["production_assist"] is False
    assert formatting["open_p0"] == []
    assert formatting["open_material_p1"] == []
    assert formatting["kr_rollout"] == "LIVE_PASS"
    assert formatting["next_action"] == "NO_ACTION_KR_LIVE_PROOF_CLOSED"
    assert state["current_commit"] == accepted_implementation_commit
    reality_gate = state["price_structure_major_sr_reality_gate"]
    assert reality_gate["status"] == "deployed_kr_live_pass_us_pending"
    assert reality_gate["instruction_commit"] == ("4a5702823da3f950b9f125bcbcfecd7c6cfa84df")
    assert reality_gate["implementation_commit"] == ("c5f1fbcb9c952c2d14ad0b178a9b33351d15b512")
    assert reality_gate["same_raw_replay"] == "PASS_20_OF_20"
    assert reality_gate["dynamic_only_major_before"] == 18
    assert reality_gate["dynamic_only_major_after"] == 0
    assert reality_gate["major_without_price_anchor"] == 0
    assert reality_gate["near_sr_changes"] == 0
    assert reality_gate["test_exact_payload_match"] == "PASS_20_OF_20"
    assert reality_gate["production_recipient_send"] == 0
    assert reality_gate["production_delivery_intent_created"] == 0
    assert reality_gate["post_deploy_replay"] == "PASS_20_OF_20"
    assert reality_gate["open_p0"] == []
    assert reality_gate["open_material_p1"] == []
    assert reality_gate["natural_major_sr_reality_gate"] == "LIVE_PASS_KR_US_PENDING"
    assert state["ai_review_mode"] == "shadow"
    assert state["ai_policy_version"] == "daily-review-v3.10"
    assert state["output_schema_version"] == 4
    assert state["security_identity_version"] == "security-identity-v2"
    assert state["financial_quality_version"] == "financial-quality-taint-v2"
    assert state["ohlcv_structure_version"] == "ohlcv-structure-v2"
    assert state["pilot_version"] == "ai-assisted-pilot-v3"
    assert state["pilot_counts_at_activation"] == {"kr": 0, "us": 0}
    assert state["pilot_current_successful_sessions"] == {"kr": 4, "us": 4}
    assert state["monitoring_state_version"] == "monitoring-state-v1"
    task_state = state["scheduled_task_contract_verification"]
    assert task_state["status"] == "passed"
    assert task_state["expected_target_count"] == 4
    assert task_state["visible_target_count"] == 4
    assert task_state["active_target_count"] == 4
    assert task_state["required_policy_version"] == "daily-review-v3.10"
    assert task_state["times_kst"] == ["08:15", "08:30", "16:15", "16:55"]
    assert task_state["manual_executions_during_promotion"] == 0
    assert state["single_delivery"] is True
    assert state["deterministic_fallback"] is True
    assert state["production_assist"] is False
    assert state["public_action_version"] == "0.4.5"
    assert state["public_action_operation_ids"] == "20/20"


def test_kr_afternoon_run42_natural_reproof_artifacts_are_closed() -> None:
    prefix = "20260827-kr-afternoon-"
    markdown_suffixes = (
        "natural-run-identity.md",
        "exactly-once.md",
        "ka20001-index-breadth.md",
        "ka20003-size-sector.md",
        "ka10051-aggregate-flow.md",
        "ka10066-pagination.md",
        "flow-reconciliation.md",
        "concentration-eligibility.md",
        "sector-numeric-registry.md",
        "ai-readiness.md",
        "krx-cross-provider.md",
        "local-first-reproof.md",
        "ai-fallback-parity.md",
        "exact-message.md",
        "evidence-utilization.md",
        "message-quality.md",
        "safety-parity.md",
        "natural-reproof-readiness.md",
        "artifact-index.md",
    )
    for suffix in markdown_suffixes:
        assert (ROOT / "docs" / "reports" / f"{prefix}{suffix}").exists()

    readiness = json.loads(
        (ROOT / "docs" / "reports" / f"{prefix}natural-reproof-readiness.json").read_text()
    )
    gates = readiness["gates"]
    assert readiness["natural_run_id"] == 42
    assert readiness["target_session"] == "2026-08-27"
    assert readiness["packet_id"] == "2026-08-27-kr-run-42-5d8d23e6fbd6"
    assert readiness["route"] == "AI"
    assert gates["KR_AFTERNOON_NATURAL"] == "LIVE_PASS"
    assert gates["KR_PACKET_INTEGRITY"] == "PASS"
    assert gates["KR_EXACTLY_ONCE"] == "PASS"
    assert gates["KR_EXACT_MESSAGE_PAYLOAD_MATCH"] == "PASS"
    assert gates["TOTAL_NUMERIC_PATHS"] == 1989
    assert gates["SUPPORTED_CANONICAL_PATHS"] == 252
    assert gates["REGISTERED_SUPPORTED_PATHS"] == 252
    assert gates["INTERNAL_ONLY_PATHS"] == 126
    assert gates["UNSUPPORTED_PATHS"] == 0
    assert gates["NUMERIC_GATE"] == "PASS"
    assert gates["READY_FOR_AI"] is True
    assert gates["KOSPI_RECONCILIATION"] == "UNRESOLVED_BASIS_OR_TAXONOMY"
    assert gates["KOSDAQ_RECONCILIATION"] == "UNRESOLVED_BASIS_OR_TAXONOMY"
    assert gates["UNRECONCILED_CONCENTRATION_PROSE"] == 0
    assert gates["KR_LOCAL_FIRST_DIGEST"] == "PASS"
    assert gates["AI_FALLBACK_LOCAL_FIRST_PARITY"] == "PASS"
    assert gates["V3_PRICE_STRUCTURE_LEAK"] == 0
    assert readiness["open_p0"] == []
    assert readiness["open_material_p1"] == []
    assert readiness["natural_kr_reproof"] == "PASS"
    assert readiness["price_structure_track_c"] == "DO_NOT_START"

    matrix = json.loads(
        (ROOT / "docs" / "reports" / f"{prefix}data-completeness-matrix.json").read_text()
    )
    assert matrix["target_session"] == "2026-08-27"
    assert len(matrix["rows"]) == 19
    assert not any(row["message_used"] == "MESSAGE_OMITTED_MATERIAL_LOSS" for row in matrix["rows"])


def test_kr_size_sector_message_selection_replay_artifacts_are_closed() -> None:
    prefix = "20260827-kr-"
    suffixes = (
        "size-sector-selection-root-cause.md",
        "size-sector-message-policy.md",
        "run42-size-sector-plan.md",
        "run42-before-after-message.md",
        "run42-ai-fallback-size-sector-parity.md",
        "run42-size-sector-provenance.md",
        "size-sector-message-quality.md",
        "size-sector-safety-parity.md",
        "size-sector-repair-readiness.md",
        "size-sector-validation.md",
        "run42-size-sector-utilization.json",
        "size-sector-repair-readiness.json",
        "size-sector-artifact-index.md",
    )
    for suffix in suffixes:
        assert (ROOT / "docs" / "reports" / f"{prefix}{suffix}").exists()

    readiness = json.loads(
        (ROOT / "docs" / "reports" / f"{prefix}size-sector-repair-readiness.json").read_text()
    )
    gates = readiness["gates"]
    assert readiness["packet_id"] == "2026-08-27-kr-run-42-5d8d23e6fbd6"
    assert gates["RUN42_OLD_MESSAGE_NEW_POLICY"] == "FAIL_AS_EXPECTED"
    assert gates["AI_FALLBACK_SIZE_STYLE_PARITY"] == "PASS"
    assert gates["AI_FALLBACK_SECTOR_PARITY"] == "PASS"
    assert gates["SIZE_STYLE_AVAILABLE_BUT_OMITTED"] == 0
    assert gates["SECTOR_EXTREMES_AVAILABLE_BUT_OMITTED"] == 0
    assert gates["UNREGISTERED_SIZE_SECTOR_NUMERIC"] == 0
    assert gates["CODE_CORRECTNESS"] == "PASS"
    assert gates["KR_SIZE_SECTOR_MESSAGE_REPAIR"] == ("REPLAY_PASS_NATURAL_REPROOF_PENDING")
    assert readiness["open_p0"] == []
    assert readiness["open_material_p1"] == []
    assert readiness["natural_kr_reproof"] == "PENDING"


def test_knowledge_checksums_and_runtime_parity_are_documented() -> None:
    investment_paths = (
        ROOT / "docs" / "knowledge" / "investment-thesis-analysis-monitoring-knowledge-v3.md",
        ROOT
        / ".agents"
        / "skills"
        / "thesis-monitor-daily-review"
        / "references"
        / "investment-thesis-analysis-monitoring-knowledge.md",
        ROOT / "docs" / "custom_gpt_knowledge_ko.md",
    )
    chart_paths = (
        ROOT / "docs" / "knowledge" / "stock-chart-value-analysis-knowledge-v1.md",
        ROOT
        / ".agents"
        / "skills"
        / "thesis-monitor-daily-review"
        / "references"
        / "stock-chart-value-analysis-knowledge-v1.md",
    )

    assert {_sha256(path) for path in investment_paths} == {INVESTMENT_SHA}
    assert {_sha256(path) for path in chart_paths} == {CHART_SHA}
    state = (ROOT / "docs" / "project-state.json").read_text()
    guide = (ROOT / "docs" / "knowledge" / "README.md").read_text()
    assert INVESTMENT_SHA in state and INVESTMENT_SHA in guide
    assert CHART_SHA in state and CHART_SHA in guide


def test_architecture_guides_record_decisions_and_readme_navigation() -> None:
    decision_docs = (
        ROOT / "docs" / "architecture" / "AI_ASSISTED_MONITORING.md",
        ROOT / "docs" / "architecture" / "OHLCV_STRUCTURE_ENGINE.md",
        ROOT / "docs" / "architecture" / "MARKET_INTELLIGENCE.md",
        ROOT / "docs" / "architecture" / "NUMERIC_PROVENANCE.md",
        ROOT / "docs" / "architecture" / "MONITORING_STATE_LIFECYCLE.md",
        ROOT / "docs" / "architecture" / "PEER_VALUATION.md",
        ROOT / "docs" / "architecture" / "NIGHT_FUTURES_SESSION_BASIS.md",
        ROOT / "docs" / "architecture" / "NIGHT_FUTURES_PUBLICATION_TELEMETRY.md",
        ROOT / "docs" / "architecture" / "CASH_FLOW_CAPITAL_EFFICIENCY.md",
        ROOT / "docs" / "architecture" / "CASH_FLOW_SHADOW_CONSUMPTION.md",
        ROOT / "docs" / "architecture" / "CASH_FLOW_RUNTIME_SHADOW_CANARY.md",
        ROOT / "docs" / "architecture" / "CASH_FLOW_BASELINE_CONSISTENCY.md",
        ROOT / "docs" / "architecture" / "CASH_FLOW_USER_VISIBLE_INTEGRATION.md",
        ROOT / "docs" / "architecture" / "WORKING_CAPITAL_SHADOW_CONSUMPTION.md",
        ROOT / "docs" / "architecture" / "WORKING_CAPITAL_RUNTIME_SHADOW_CANARY.md",
        ROOT / "docs" / "architecture" / "WORKING_CAPITAL_USER_VISIBLE_PREINTEGRATION.md",
        ROOT / "docs" / "architecture" / "PRICE_STRUCTURE_WAVE_FIB_V3.md",
        ROOT / "docs" / "architecture" / "OHLCV_LONG_HISTORY_CONTRACT.md",
        ROOT / "docs" / "architecture" / "PRIMARY_MONTHLY_WAVE_HYPOTHESIS.md",
        ROOT / "docs" / "architecture" / "WAVE_FIBONACCI_SOURCE_PROVENANCE.md",
        ROOT / "docs" / "architecture" / "MULTI_TIMEFRAME_SR_CONFLUENCE_V3.md",
        ROOT / "docs" / "architecture" / "TECHNICAL_ZONE_EVIDENCE_FAMILIES.md",
        ROOT / "docs" / "architecture" / "PRICE_STRUCTURE_V3_SHADOW_POLICY.md",
        ROOT / "docs" / "operations" / "AI_ASSISTED_PILOT.md",
        ROOT / "docs" / "knowledge" / "README.md",
    )
    for path in decision_docs:
        text = path.read_text()
        assert "## Problem" in text
        assert "## Decision" in text
        assert "## Why" in text
        assert "## Rejected Alternative" in text
        assert "## Safety Constraint" in text

    readme = (ROOT / "README.md").read_text()
    for relative in (
        "docs/PROJECT_HANDOFF.md",
        "docs/architecture/AI_ASSISTED_MONITORING.md",
        "docs/architecture/OHLCV_STRUCTURE_ENGINE.md",
        "docs/architecture/MARKET_INTELLIGENCE.md",
        "docs/architecture/NUMERIC_PROVENANCE.md",
        "docs/architecture/MONITORING_STATE_LIFECYCLE.md",
        "docs/architecture/PEER_VALUATION.md",
        "docs/architecture/CASH_FLOW_CAPITAL_EFFICIENCY.md",
        "docs/architecture/CASH_FLOW_SHADOW_CONSUMPTION.md",
        "docs/architecture/CASH_FLOW_RUNTIME_SHADOW_CANARY.md",
        "docs/architecture/CASH_FLOW_USER_VISIBLE_INTEGRATION.md",
        "docs/architecture/WORKING_CAPITAL_SHADOW_CONSUMPTION.md",
        "docs/architecture/WORKING_CAPITAL_RUNTIME_SHADOW_CANARY.md",
        "docs/architecture/WORKING_CAPITAL_USER_VISIBLE_PREINTEGRATION.md",
        "docs/architecture/NIGHT_FUTURES_SESSION_BASIS.md",
        "docs/architecture/NIGHT_FUTURES_PUBLICATION_TELEMETRY.md",
        "docs/architecture/PRICE_STRUCTURE_WAVE_FIB_V3.md",
        "docs/architecture/OHLCV_LONG_HISTORY_CONTRACT.md",
        "docs/architecture/PRIMARY_MONTHLY_WAVE_HYPOTHESIS.md",
        "docs/architecture/WAVE_FIBONACCI_SOURCE_PROVENANCE.md",
        "docs/architecture/MULTI_TIMEFRAME_SR_CONFLUENCE_V3.md",
        "docs/architecture/TECHNICAL_ZONE_EVIDENCE_FAMILIES.md",
        "docs/architecture/PRICE_STRUCTURE_V3_SHADOW_POLICY.md",
        "docs/operations/AI_ASSISTED_PILOT.md",
        "docs/operations/SCHEDULED_TASK_CONTRACTS.md",
        "docs/knowledge/README.md",
        "docs/NEXT_SESSION_PROMPT.md",
        "docs/project-state.json",
    ):
        assert relative in readme


def test_documentation_relative_links_resolve_and_contains_no_secrets() -> None:
    markdown_paths = [path for path in DOCUMENTS if path.suffix == ".md"]
    markdown_paths.extend([ROOT / "README.md", ROOT / "docs" / "ai_review_project_handoff.md"])
    secret_assignment = re.compile(
        r"(?i)(?:api[_-]?key|token|secret|password|chat[_-]?id)"
        r"[ \t]*[:=][ \t]*['\"]?[A-Za-z0-9_\-]{12,}"
    )

    for path in markdown_paths:
        text = path.read_text()
        assert "/Users/" not in text
        assert "/home/" not in text
        assert secret_assignment.search(text) is None
        for raw_target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            target = raw_target.split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            assert (path.parent / target).resolve().exists(), (path, target)


def test_fail_closed_kr_preenable_artifacts_are_complete() -> None:
    reports = ROOT / "docs" / "reports"
    required = (
        "20260827-kr-preenable-target-session.md",
        "20260827-kr-preenable-data-collection.md",
        "20260827-kr-preenable-numeric-provenance.md",
        "20260827-kr-preenable-reconciliation.md",
        "20260827-kr-preenable-market-digest-plan.md",
        "20260827-kr-preenable-ai-fallback-parity.md",
        "20260827-kr-preenable-test-sink-safety.md",
        "20260827-kr-preenable-test-delivery.md",
        "20260827-kr-preenable-exact-test-message.md",
        "20260827-kr-preenable-message-quality.md",
        "20260827-kr-preenable-gate-matrix.md",
        "20260827-kr-size-sector-enablement-action.md",
        "20260827-kr-size-sector-post-enable-smoke.md",
        "20260827-kr-size-sector-natural-proof-status.md",
        "20260827-kr-preenable-safety-parity.md",
        "20260827-kr-preenable-artifact-index.md",
    )
    assert all((reports / name).exists() for name in required)
    provenance = (reports / "20260827-kr-preenable-numeric-provenance.md").read_text()
    assert provenance.count("market:cross-section:sector:") == 10

    evidence = json.loads((reports / "20260827-kr-preenable-gate-matrix.json").read_text())
    gates = evidence["gates"]
    assert gates["PREENABLE_DATA_COLLECTION"] == "PASS"
    assert gates["NUMERIC_GATE"] == "PASS"
    assert gates["AI_FALLBACK_SIZE_STYLE_PARITY"] == "PASS"
    assert gates["AI_FALLBACK_SECTOR_PARITY"] == "PASS"
    assert gates["TEST_SINK_AVAILABLE"] == "NO"
    assert gates["TEST_DELIVERY_COUNT"] == 0
    assert gates["PRODUCTION_DELIVERY_INTENT_CREATED"] == 0
    assert gates["ENABLEMENT_ACTION"] == "DO_NOT_ENABLE"
    assert gates["PRICE_STRUCTURE_RUNTIME_ARMED"] == 0
    assert evidence["open_p0"] == []
    assert evidence["open_material_p1"] == ["dedicated_test_sink_not_configured"]


def test_kr_top3_price_structure_preenablement_artifacts_are_complete() -> None:
    reports = ROOT / "docs" / "reports"
    markdown = (
        "20260827-kr-top3-sector-policy.md",
        "20260827-kr-top3-sector-run42-replay.md",
        "20260827-kr-price-structure-selective-scope.md",
        "20260827-kr-price-structure-current-replay.md",
        "20260827-kr-price-structure-per-ticker-audit.md",
        "20260827-kr-test-sink-isolation.md",
        "20260827-kr-market-test-exact-message.md",
        "20260827-kr-stock-test-exact-messages.md",
        "20260827-kr-test-message-quality.md",
        "20260827-kr-rollout-gate-matrix.md",
        "20260827-kr-only-enablement-action.md",
        "20260827-kr-post-enable-smoke.md",
        "20260827-kr-natural-proof-status.md",
        "20260827-kr-rollout-safety-parity.md",
        "20260827-kr-rollout-artifact-index.md",
        "20260827-kr-price-structure-numeric-provenance.md",
        "20260827-kr-rollout-validation.md",
    )
    machine_readable = (
        "20260827-kr-top3-sector-selection.json",
        "20260827-kr-price-structure-per-ticker-audit.json",
        "20260827-kr-rollout-gate-matrix.json",
        "20260827-kr-rollout-status.json",
    )
    assert all((reports / name).exists() for name in (*markdown, *machine_readable))

    evidence = json.loads((reports / "20260827-kr-rollout-gate-matrix.json").read_text())
    gates = evidence["gates"]
    assert gates["KR_TOP3_SECTOR_POLICY"] == "PASS"
    assert gates["SELECTIVE_ELIGIBILITY_ROUTING"] == "PASS"
    assert gates["TEST_SINK_AVAILABLE"] == "NO"
    assert gates["PRODUCTION_DELIVERY_INTENT_CREATED"] == 0
    assert gates["KR_MARKET_TOP3_ENABLEMENT"] == "DO_NOT_ENABLE"
    assert gates["KR_PRICE_STRUCTURE_ENABLEMENT"] == "DO_NOT_ENABLE"
    assert gates["US_PRICE_STRUCTURE_ENABLED"] == 0
    assert evidence["open_p0"] == []
    assert evidence["open_material_p1"] == ["dedicated_test_sink_not_configured"]


def test_us_market_and_price_structure_rollout_artifacts_are_complete() -> None:
    reports = ROOT / "docs" / "reports"
    market = (
        "20260828-us-index-block-policy.md",
        "20260828-us-night-futures-root-cause.md",
        "20260828-us-night-futures-session-mapping.md",
        "20260828-us-night-futures-provenance.md",
        "20260828-us-full-message-layout.md",
        "20260828-us-full-message-before-after.md",
        "20260828-us-full-message-ai-fallback-parity.md",
        "20260828-us-full-message-evidence-utilization.md",
        "20260828-us-full-message-test-delivery.md",
        "20260828-us-full-message-exact-test-message.md",
        "20260828-us-full-message-refinement-history.md",
        "20260828-us-full-message-quality.md",
        "20260828-us-full-message-safety-parity.md",
        "20260828-us-full-message-readiness.md",
        "20260828-us-full-message-natural-proof-status.md",
        "20260828-us-full-message-artifact-index.md",
        "20260828-us-full-message-evidence-utilization.json",
        "20260828-us-full-message-readiness.json",
    )
    price = (
        "20260828-us-price-structure-scope.md",
        "20260828-us-price-structure-current-universe.md",
        "20260828-us-price-structure-coverage.md",
        "20260828-us-price-structure-per-ticker.md",
        "20260828-us-price-structure-ai-fallback-parity.md",
        "20260828-us-price-structure-security-basis.md",
        "20260828-us-price-structure-test-delivery.md",
        "20260828-us-price-structure-exact-test-messages.md",
        "20260828-us-price-structure-message-quality.md",
        "20260828-us-price-structure-preenable-readiness.md",
        "20260828-us-price-structure-operating-promotion.md",
        "20260828-us-price-structure-post-enable-smoke.md",
        "20260828-us-price-structure-natural-proof-status.md",
        "20260828-us-price-structure-safety-parity.md",
        "20260828-us-price-structure-rollback.md",
        "20260828-us-price-structure-artifact-index.md",
        "20260828-us-price-structure-per-ticker.json",
        "20260828-us-price-structure-preenable-readiness.json",
        "20260828-us-price-structure-natural-proof-status.json",
    )
    assert all((reports / name).exists() for name in (*market, *price))

    market_ready = json.loads((reports / "20260828-us-full-message-readiness.json").read_text())
    assert market_ready["state"] == "DEPLOYED_AWAITING_NATURAL_PROOF"
    assert market_ready["test_delivery"] == "PASS_1_OF_1"
    assert market_ready["open_p0"] == []
    assert market_ready["open_material_p1"] == []

    price_ready = json.loads(
        (reports / "20260828-us-price-structure-preenable-readiness.json").read_text()
    )
    assert price_ready["current_us_monitored_stock_count"] == 13
    assert price_ready["eligibility_counts"] == {"ELIGIBLE_SR_ONLY": 13}
    assert price_ready["test_delivery"] == "PASS_13_OF_13"
    assert price_ready["post_enable_all_us_stocks"] == "PASS"
    assert price_ready["post_enable_kr_price_structure_diff"] == 0
    assert price_ready["us_price_structure_enabled"] is True
    assert price_ready["state"] == "ENABLED_AWAITING_NATURAL_PROOF"
    assert price_ready["open_p0"] == []
    assert price_ready["open_material_p1"] == []

    for receipt_name in (
        "20260828-us-full-message-test-receipt.json",
        "20260828-us-price-structure-test-receipt.json",
    ):
        receipt_text = (reports / receipt_name).read_text()
        assert "chat_id" not in receipt_text
        assert "bot_token" not in receipt_text
        assert "authorization" not in receipt_text.lower()
