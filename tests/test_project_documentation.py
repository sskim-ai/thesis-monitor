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
    ROOT / "docs" / "architecture" / "FIB_CONFLUENCE_RENDER_EQUIVALENCE.md",
    ROOT / "docs" / "architecture" / "CURRENT_SR_VS_STORED_PRICE_RULES.md",
    ROOT / "docs" / "architecture" / "LEGACY_TECHNICAL_PROSE_SUPPRESSION.md",
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
        "codex/20260827-us-morning-natural-market-data-review"
    )
    assert state["current_phase"] == (
        "us_morning_natural_market_data_material_p1_found_stop"
    )
    assert state["last_completed_phase"] == (
        "us_morning_natural_market_data_read_only_review"
    )
    assert state["next_default_phase"] == "bounded_us_market_repair"
    implementation_commit = "848eb80f6ce6504a9a855973b591ee0749167514"
    detector_implementation_commit = "3685aa991589ca0e7cc560104d4ebf8289e3f91d"
    preenablement_commit = "84f8f549bc8fa0338309a84b23b2738f2e357646"
    prior_price_structure_commit = "631e82f202b6f081866ef83c8b67b2138a8b51d8"
    prior_fibonacci_commit = "0dfef76bba606f018893d6e68e7beaf410aa7438"
    assert state["deployed_code_commit"] == implementation_commit
    assert state["main_code_commit"] == implementation_commit
    assert state["operating_code_commit"] == implementation_commit
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
    assert state["contracts"]["deterministic_sr_base_layer"] == (
        "deterministic-sr-base-layer-v1"
    )
    assert state["contracts"]["sr_proximity_relevance_gate"] == (
        "sr-proximity-relevance-gate-v1"
    )
    assert state["contracts"]["price_structure_v3_current_data_shadow_validation"] == (
        "price-structure-v3-current-data-shadow-validation-v1"
    )
    assert state["contracts"]["price_structure_v3_renderer_ownership"] == (
        "price-structure-v3-renderer-ownership-v1"
    )
    assert state["contracts"]["legacy_technical_token_detection"] == (
        "legacy-technical-token-detection-v1"
    )
    current_data = state["price_structure_v3_current_data_shadow_message_validation"]
    assert current_data["status"] == "validated_ready_not_armed"
    assert current_data["target_sessions"] == {"kr": "2026-08-26", "us": "2026-08-25"}
    assert current_data["mandatory_controls"] == "10/10_PASS"
    assert current_data["current_runtime_visible_diff"] == 0
    assert current_data["production_enabled"] is False
    renderer = state["price_structure_v3_renderer_integration_micro_repair"]
    assert renderer["status"] == "integrated_ready_not_armed"
    assert renderer["implementation_commit"] == (
        "4246efb4f8afa3516402d1df7864967c177ac6e7"
    )
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
    assert state["contracts"]["market_context_adapter"] == (
        "market-context-adapter-v1"
    )
    assert state["contracts"]["structured_market_context"] == (
        "structured-market-context-v1"
    )
    assert state["contracts"]["nasdaq_official_exchange_breadth"] == (
        "nasdaq-official-exchange-breadth-v1"
    )
    assert state["contracts"]["kiwoom_kr_market_context"] == (
        "kiwoom-kr-market-context-v1"
    )
    assert state["contracts"]["kr_market_flow_reconciliation"] == (
        "kr-market-flow-reconciliation-v1"
    )
    assert state["contracts"]["kr_market_flow_concentration"] == (
        "kr-market-flow-concentration-v1"
    )
    assert state["contracts"]["message_quality_v2"] == "message-quality-v2"
    assert state["contracts"]["market_research_seed_adapter"] == (
        "market-research-seed-adapter-v1"
    )
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
    assert state["contracts"]["packet_bound_delivery_intent"] == (
        "packet-bound-delivery-intent-v1"
    )
    assert state["contracts"]["kr_production_packet_persistence"] == (
        "kr-production-packet-persistence-v1"
    )
    assert state["contracts"]["shadow_cohort_readiness"] == (
        "shadow-cohort-readiness-v1"
    )
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
    assert state["contracts"]["kr_market_digest_quality"] == (
        "kr-market-digest-quality-v1"
    )
    assert state["contracts"]["entity_specific_synthesis"] == (
        "entity-specific-synthesis-v1"
    )
    assert state["contracts"]["cross_message_synthesis_specificity"] == (
        "cross-message-synthesis-specificity-v1"
    )
    assert state["contracts"]["price_only_ai_anchor_packet"] == (
        "price-only-ai-anchor-packet-v1"
    )
    assert state["contracts"]["variable_ai_swing_anchor_selection"] == (
        "variable-ai-swing-anchor-selection-v1"
    )
    assert state["contracts"]["ai_anchor_stability_policy"] == (
        "ai-anchor-stability-policy-v1"
    )
    assert state["contracts"]["fibonacci_sr_ownership"] == (
        "fibonacci-sr-ownership-v1"
    )
    assert state["contracts"]["canonical_swing_structure_candidate"] == (
        "canonical-swing-structure-candidate-v1"
    )
    assert state["contracts"]["fibonacci_valid_abstention"] == (
        "fibonacci-valid-abstention-v1"
    )
    assert state["contracts"]["ai_anchor_consensus_policy"] == (
        "ai-anchor-consensus-policy-v1"
    )
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
    assert state["contracts"]["ohlcv_1200_backfill_cache"] == (
        "ohlcv-1200-backfill-cache-v1"
    )
    assert state["contracts"]["wave_degree_current_cycle"] == (
        "wave-degree-current-cycle-v1"
    )
    assert state["contracts"]["price_structure_v3_ai_feedback_loop"] == (
        "price-structure-v3-ai-feedback-loop-v1"
    )
    assert state["contracts"]["wave_hypothesis_equivalence_class"] == (
        "wave-hypothesis-equivalence-class-v1"
    )
    assert state["contracts"]["fib_family_endpoint_dependency"] == (
        "fib-family-endpoint-dependency-v1"
    )
    assert state["contracts"]["fib_family_consensus"] == (
        "fib-family-consensus-v1"
    )
    assert state["contracts"]["family_consensus_membership_audit"] == (
        "family-consensus-membership-audit-v1"
    )
    assert state["contracts"]["price_structure_v3_ambiguity_set"] == (
        "price-structure-v3-ambiguity-set-v1"
    )
    assert state["contracts"]["family_filtered_confluence"] == (
        "family-filtered-confluence-v1"
    )
    bounded_quality = state[
        "kr_market_digest_us_entity_specific_synthesis_bounded_repair"
    ]
    assert bounded_quality["instruction_commit"] == (
        "8cf5226ca0c5ae5553fb06b24399462ea3cf6088"
    )
    assert bounded_quality["implementation_commit"] == (
        "f2326c39485e600bca2cee15747deeb8465c5c8a"
    )
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
    assert fibonacci_anchor["instruction_commit"] == (
        "d9e6e2327f0f32256a1bd0d8caf2c0b0f1faf890"
    )
    assert fibonacci_anchor["implementation_commit"] == (
        "9ac9a3cf2f6c759fa73ba5cbee6ab55c08ee1901"
    )
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
    assert fibonacci_consensus["instruction_commit"] == (
        "39cab7ed8b1cb3bebea1bd1240498caa454bd09a"
    )
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
    assert price_structure_v3["instruction_commit"] == (
        "b0f81c8e16f588e314f93eb6097370e85f285241"
    )
    assert price_structure_v3["implementation_commit"] == prior_price_structure_commit
    assert price_structure_v3["implementation_github_actions_run"] == 32945710995
    assert price_structure_v3["implementation_github_actions_status"] == (
        "passed_test_and_lint"
    )
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
    assert price_structure_v3["family_consensus_gates"][
        "unstable_source_in_confluence"
    ] == 0
    assert price_structure_v3["sk_hynix_family_consensus"][
        "full_hypothesis_stability"
    ] == "MATERIAL_VARIATION"
    assert price_structure_v3["sk_hynix_family_consensus"][
        "family_level_price_structure"
    ] == "PASS"
    assert price_structure_v3["true_conflict_controls"] == {
        "TSLA": "PASS_ZERO_SAFE_FAMILIES",
        "TSM_W3_DEPENDENCY": "PASS",
    }
    assert price_structure_v3["selected_but_not_fed_to_engine"] == 0
    assert price_structure_v3["unstable_fibonacci_user_visible_eligible"] == 0
    assert price_structure_v3["sk_hynix_reference"] == (
        "REFERENCE_MATCH_FAMILY_LEVEL_SAFE_SUBSET"
    )
    assert price_structure_v3["price_structure_wave_fib_v3"] == (
        "INTEGRATED_READY_NOT_ARMED"
    )
    assert price_structure_v3["price_structure_v3_family_consensus"] == (
        "INTEGRATED_READY_NOT_ARMED"
    )
    assert price_structure_v3["production_enablement_ready"] == "YES"
    assert price_structure_v3["open_p0"] == []
    assert price_structure_v3["open_material_p1"] == []
    assert price_structure_v3["current_user_visible_message_diff"] == 0
    assert price_structure_v3["production_assist"] is False
    preenablement = state["price_structure_v3_preenablement_micro_repair"]
    assert preenablement["instruction_commit"] == (
        "38b5fbca8a7264e3b73ef78c121b6ed6758c3ad8"
    )
    assert preenablement["implementation_commit"] == preenablement_commit
    assert preenablement["membership_contract"] == (
        "family-consensus-membership-audit-v1"
    )
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
    assert sr_completeness["instruction_commit"] == (
        "7267ca1d3e518d39986941bfda1d6447560db344"
    )
    assert sr_completeness["implementation_commit"] == (
        "176f3e73eb097fac99f4038a8987b610954804cc"
    )
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
    assert advancement["phase_9_1e_1_inventory_user_visible"] == (
        "ENABLED_PENDING_NATURAL"
    )
    assert advancement["phase_9_1e_1_trade_ar_user_visible"] == (
        "OFF_PENDING_NATURAL_PROOF"
    )
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
    assert macro_temporal["instruction_commit"] == (
        "951558c0ec79f84b739eff1cbafd2870eb6f3fba"
    )
    assert macro_temporal["implementation_commit"] == (
        "68a6c39a098380d8a22de5b4d784c730818e9b04"
    )
    assert macro_temporal["false_today_claims_after"] == 0
    assert macro_temporal["open_p0"] == 0
    assert macro_temporal["open_material_p1"] == 0
    shadow_gate = state["kr_shadow_gate_packet_repair"]
    assert shadow_gate["status"] == "deployed_pending_natural"
    assert shadow_gate["root_cause_branch"] == "C"
    assert shadow_gate["instruction_commit"] == (
        "7da8d8866a9b7aafc8c010424cdbc4192de46cbb"
    )
    assert shadow_gate["implementation_commit"] == (
        "64086c4af7735dcbe2fd3f5093f4167952a280e0"
    )
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
    assert common_ai_core["free_analyst_adaptive_mode"] == (
        "free_analyst_adaptive_canary"
    )
    assert common_ai_core["free_analyst_adaptive_canary"] == (
        "enabled_pending_natural"
    )
    assert common_ai_core["free_analyst_adaptive_full"] == "off"
    assert common_ai_core["kr_canary_natural"] == "not_observed"
    assert common_ai_core["us_canary_natural"] == "not_observed"
    assert common_ai_core["open_research_production_integration"] == 0
    assert common_ai_core["open_p0"] == []
    assert common_ai_core["open_material_p1"] == []
    structured_quality = state["structured_data_quality_v2"]
    assert structured_quality["kr_structured_acquisition"] == "PARTIAL"
    assert structured_quality["us_structured_acquisition"] == "PARTIAL"
    assert structured_quality["kr_structured_context_value_add"] == (
        "NO_MATERIAL_VALUE"
    )
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
    assert market_adapter["structured_adapter_production"] == (
        "DEPLOYED_PENDING_NATURAL"
    )
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
    assert phase_91e1["work_instruction_commit"] == (
        "880e7a9834439971f53b8a7bc0712d0ece26854d"
    )
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
    assert master["status"] == "bounded_us_market_repair_required"
    assert master["instruction_commit"] == (
        "e76a7d6b5e8ddc110d3228cfd5e55f26dbdb1e1d"
    )
    assert master["integration_code_commit"] == implementation_commit
    assert master["track_a"]["status"] == "bounded_repair_required"
    assert master["track_a"]["natural_run_id"] == 41
    assert master["track_a"]["natural_packet"] == (
        "2026-08-27-us-run-41-ae4f42c23abc"
    )
    assert master["track_a"]["open_material_p1"] == [
        "us_current_session_market_evidence_omitted_from_natural_digest"
    ]
    assert master["track_b"]["status"] == "replay_pass_natural_reproof_pending"
    assert master["track_b"]["open_material_p1"] == []
    assert master["track_c"] == {
        "status": "do_not_start",
        "branch": None,
        "production_armed": False,
    }
    assert master["price_structure_v3"] == "integrated_ready_not_armed"
    assert master["open_p0"] == []
    assert master["open_material_p1"] == [
        "us_current_session_market_evidence_omitted_from_natural_digest"
    ]
    assert master["production_assist"] is False
    bounded_repair = state["kr_bounded_local_first_numeric_registry_repair"]
    assert bounded_repair["status"] == "replay_pass_natural_reproof_pending"
    assert bounded_repair["instruction_commit"] == (
        "f6ba660048d3fa520e3aeb43d04036c119764292"
    )
    assert bounded_repair["integration_code_commit"] == implementation_commit
    assert bounded_repair["numeric_paths"] == {
        "total": 1961,
        "registered": 1961,
        "unsupported": 0,
        "prose_allowed": 1472,
        "denied": 489,
    }
    assert bounded_repair["open_p0"] == []
    assert bounded_repair["open_material_p1"] == []
    assert bounded_repair["natural_kr_reproof"] == "PENDING"
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
    assert state["current_commit"] == implementation_commit
    assert state["ai_review_mode"] == "shadow"
    assert state["ai_policy_version"] == "daily-review-v3.10"
    assert state["output_schema_version"] == 4
    assert state["security_identity_version"] == "security-identity-v2"
    assert state["financial_quality_version"] == "financial-quality-taint-v2"
    assert state["ohlcv_structure_version"] == "ohlcv-structure-v2"
    assert state["pilot_version"] == "ai-assisted-pilot-v3"
    assert state["pilot_counts_at_activation"] == {"kr": 0, "us": 0}
    assert state["pilot_current_successful_sessions"] == {"kr": 3, "us": 4}
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
