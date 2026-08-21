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
    ROOT / "docs" / "architecture" / "RUNTIME_REASONING_OWNERSHIP.md",
    ROOT / "docs" / "architecture" / "CASH_FLOW_CAPITAL_EFFICIENCY.md",
    ROOT / "docs" / "architecture" / "CASH_FLOW_SHADOW_CONSUMPTION.md",
    ROOT / "docs" / "architecture" / "CASH_FLOW_RUNTIME_SHADOW_CANARY.md",
    ROOT / "docs" / "architecture" / "CASH_FLOW_BASELINE_CONSISTENCY.md",
    ROOT / "docs" / "operations" / "AI_ASSISTED_PILOT.md",
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
    assert state["experimental_branch"] == (
        "codex/phase-9-0d-1-baseline-cash-flow-consistency-repair"
    )
    assert state["current_phase"] == (
        "phase_9_0d_1_baseline_cash_flow_consistency_closed"
    )
    assert state["last_completed_phase"] == (
        "phase_9_0d_1_baseline_cash_flow_consistency_repair"
    )
    assert state["next_default_phase"] == (
        "phase_9_0e_selective_cash_flow_user_visible_integration"
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
    assert state["persistent_gaps"]["reasoning_ownership"] == (
        "LIVE_PASS_RUN29"
    )
    assert state["contracts"]["runtime_specificity"] == ("runtime-message-specificity-v2")
    assert state["contracts"]["runtime_reasoning_ownership"] == ("runtime-reasoning-ownership-v1")
    assert state["contracts"]["numeric_summary_ownership"] == (
        "numeric-summary-ownership-v1"
    )
    assert state["contracts"]["typed_template_skeleton"] == (
        "typed-template-skeleton-v1"
    )
    assert state["contracts"]["canonical_supply_flow_tuple"] == (
        "canonical-supply-flow-tuple-v1"
    )
    assert state["contracts"]["numeric_primary_owner"] == (
        "numeric-primary-owner-v1"
    )
    assert state["contracts"]["cash_flow_capital_efficiency"] == (
        "cash-flow-capital-efficiency-v1"
    )
    assert state["contracts"]["cash_flow_shadow_consumption"] == (
        "cash-flow-shadow-consumption-v1"
    )
    assert state["contracts"]["cash_flow_runtime_shadow_canary"] == (
        "cash-flow-runtime-shadow-canary-v1"
    )
    assert state["contracts"]["baseline_cash_flow_claim_consistency"] == (
        "baseline-cash-flow-claim-consistency-v1"
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
    phase_90a = state["phase_9_0a_cash_flow_capital_efficiency"]
    assert phase_90a["status"] == "architecture_closed_ready_for_phase_9_0b"
    assert phase_90a["active_universe"] == 20
    assert phase_90a["phase_9_0b_ready"] is True
    assert phase_90a["runtime_behavior_changed"] is False
    assert phase_90a["user_visible_integration"] is False
    phase_90b = state["phase_9_0b_canonical_cash_flow_core"]
    assert phase_90b["status"] == (
        "canonical_core_implemented_shadow_ready_for_phase_9_0c"
    )
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
    assert phase_90d["work_instruction_commit"] == (
        "a24e4f2210f944fa7c43d8dbf8be1d1a8e652164"
    )
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
    assert state["persistent_gaps"]["krx_open_api"] == (
        "APPROVED_TELEMETRY_ONLY_OPERATING_USER_VISIBLE_NOT_INTEGRATED"
    )
    assert state["krx"]["exact_slot_capture"] == (
        "operating_telemetry_only_pending_natural"
    )
    assert state["krx"]["user_visible_integration"] is False
    assert state["persistent_gaps"]["night_futures_session_basis"] == (
        "CLOSED_RETROSPECTIVE_LIVE_FAIL_CLOSED_RUN28"
    )
    assert state["persistent_gaps"]["night_futures_preceding_day_calendar_lookup"] == (
        "CLOSED_RETROSPECTIVE_PENDING_NATURAL"
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
        ROOT / "docs" / "architecture" / "CASH_FLOW_CAPITAL_EFFICIENCY.md",
        ROOT / "docs" / "architecture" / "CASH_FLOW_SHADOW_CONSUMPTION.md",
        ROOT / "docs" / "architecture" / "CASH_FLOW_RUNTIME_SHADOW_CANARY.md",
        ROOT / "docs" / "architecture" / "CASH_FLOW_BASELINE_CONSISTENCY.md",
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
        "docs/architecture/NIGHT_FUTURES_SESSION_BASIS.md",
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
