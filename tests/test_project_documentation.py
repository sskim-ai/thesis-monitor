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
    ROOT / "docs" / "architecture" / "US_MARKET_CONTEXT_ADAPTER.md",
    ROOT / "docs" / "architecture" / "MARKET_RESEARCH_SEED_ADAPTERS.md",
    ROOT / "docs" / "architecture" / "PRODUCTION_RESEARCH_CONNECTOR_BOUNDARY.md",
    ROOT / "docs" / "architecture" / "FREE_ANALYST_PRODUCTION_INTEGRATION.md",
    ROOT / "docs" / "architecture" / "ADAPTIVE_RENDERER_PRODUCTION.md",
    ROOT / "docs" / "architecture" / "FREE_ANALYST_CANARY_POLICY.md",
    ROOT / "docs" / "operations" / "AI_ASSISTED_PILOT.md",
    ROOT / "docs" / "operations" / "CASH_FLOW_USER_VISIBLE_KILL_SWITCH.md",
    ROOT / "docs" / "operations" / "WORKING_CAPITAL_USER_VISIBLE_KILL_SWITCH.md",
    ROOT / "docs" / "knowledge" / "README.md",
)
INVESTMENT_SHA = "559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18"
CHART_SHA = "beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_persistent_handoff_artifacts_and_state_are_current() -> None:
    assert all(path.exists() for path in DOCUMENTS)
    state = json.loads((ROOT / "docs" / "project-state.json").read_text())

    assert state["repository"] == "sskim-ai/thesis-monitor"
    assert state["branch"] == "main"
    assert state["experimental_branch"] == "codex/kr-us-market-adapters"
    assert state["current_phase"] == (
        "common_market_adapter_v1_production_pending_natural"
    )
    assert state["last_completed_phase"] == (
        "kr_valuation_numeric_ref_repair_and_market_adapter_implementation"
    )
    assert state["next_default_phase"] == (
        "us_structured_market_adapter_natural_canary_review"
    )
    assert state["deployed_code_commit"] == "HEAD"
    assert state["main_code_commit"] == "HEAD"
    assert state["operating_code_commit"] == "HEAD"
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
    assert state["contracts"]["market_context_adapter"] == (
        "market-context-adapter-v1"
    )
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
    market_adapter = state["common_market_adapter_v1"]
    assert market_adapter["status"] == "production_pending_natural"
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
    assert state["current_commit"] == "HEAD"
    assert state["current_commit_resolution"] == "git rev-parse HEAD"
    assert state["ai_review_mode"] == "shadow"
    assert state["ai_policy_version"] == "daily-review-v3.10"
    assert state["output_schema_version"] == 4
    assert state["security_identity_version"] == "security-identity-v2"
    assert state["financial_quality_version"] == "financial-quality-taint-v2"
    assert state["ohlcv_structure_version"] == "ohlcv-structure-v2"
    assert state["pilot_version"] == "ai-assisted-pilot-v3"
    assert state["pilot_counts_at_activation"] == {"kr": 0, "us": 0}
    assert state["pilot_current_successful_sessions"] == {"kr": 3, "us": 3}
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
